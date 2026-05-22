# Registry

The `registry<Key, Tag, Payload>` is a per-type singleton that **interns** values: every distinct `Key` gets one stable 4-byte ID, and asking to intern the same key again returns the existing ID. This is useful for collapsing many references to the same value (chromosome names, transcript/gene IDs, sample identifiers seen thousands of times across grove entries) down to a single ID that can be stored alongside grove keys.

The full template signature is:

```cpp
template<registry_value Key, typename Tag = void, typename Payload = Key>
class registry;
```

- **`Key`** — the identity used for deduplication. Must satisfy the `registry_value` concept (see below).
- **`Tag`** *(optional, default `void`)* — phantom type that discriminates singletons; see [Tagged Singletons](#tagged-singletons).
- **`Payload`** *(optional, default `Key`)* — the value stored against each ID. When `Payload != Key`, identity is a subset of the stored record; see [Storing Richer Payloads](#storing-richer-payloads).

The default `registry<Key>` (with both `Tag` and `Payload` defaulted) preserves the original "one singleton per `Key`" behavior, so existing call sites are unaffected.

```cpp
#include <genogrove/data_type/registry.hpp>
#include <iostream>
#include <sstream>
#include <string>

namespace gdt = genogrove::data_type;

int main() {
    // 1. Get the singleton registry for std::string
    auto& reg = gdt::registry<std::string>::instance();

    // 2. Intern values — dedup-on-insert
    auto id1 = reg.intern("chr1");   // 0 (new)
    auto id2 = reg.intern("chr1");   // 0 (existing — same ID as id1)
    auto id3 = reg.intern("chr2");   // 1 (new)

    // 3. Probe without inserting
    if (auto maybe = reg.find("chr3"); !maybe) {
        std::cout << "chr3 has not been interned\n";
    }
    auto found = reg.find("chr1");   // std::optional<id_type>{0}

    // 4. Resolve an ID back to its value (const access only)
    const std::string& chrom = reg.get(id1);  // "chr1"

    // 5. Registry state
    size_t count = reg.size();          // 2
    bool is_empty = reg.empty();        // false
    bool has_id1 = reg.contains(id1);   // true
    bool has_999 = reg.contains(999);   // false

    // 6. Use with grove — store 4-byte IDs instead of full strings
    // grove<interval, uint32_t> g;
    // g.insert_data("chr1", interval{100, 200}, id1);

    // 7. Serialization
    std::ostringstream oss(std::ios::binary);
    reg.serialize(oss);

    // 8. Deserialization (clears the singleton and repopulates it)
    std::istringstream iss(oss.str(), std::ios::binary);
    auto& restored = gdt::registry<std::string>::deserialize(iss);

    // 9. Clear the registry (invalidates all IDs — use with caution)
    reg.clear();
    // Or via static method:
    gdt::registry<std::string>::reset();

    return 0;
}
```

## Tagged Singletons

Each `(Key, Tag, Payload)` triple has its own singleton with an independent ID space. The `Tag` parameter is a phantom type — it never appears in the registry's body, contributes no storage or serialization, and has zero runtime cost. Its only purpose is to discriminate singletons that would otherwise collide.

Use a tag when two unrelated pools in the same binary share the same `Key` type and must not share an ID space:

```cpp
using transcript_registry = gdt::registry<std::string, struct transcript_tag>;
using source_registry     = gdt::registry<std::string, struct source_tag>;

transcript_registry::instance().intern("ENST00000001"); // 0 in transcript pool
source_registry::instance().intern("HAVANA");           // 0 in source pool (separate)
```

Without the tag, both pools would collapse into a single `registry<std::string>` singleton and IDs would collide.

The bare form `registry<std::string>` remains the right default whenever a single pool is what you actually want (e.g. one global pool of chromosome names).

## Storing Richer Payloads

When identity is a subset of a larger record — e.g. `gene_id` keying a struct of gene fields — set `Payload` to the full record type:

```cpp
struct gene_info {
    std::string gene_name;
    std::string gene_biotype;
};
using gene_reg = gdt::registry<std::string, void, gene_info>;

auto id1 = gene_reg::instance().intern("ENSG001", {"FOO", "protein_coding"});
auto id2 = gene_reg::instance().intern("ENSG001", {"placeholder", ""});
// id1 == id2; the placeholder payload is silently dropped.
const gene_info& g = gene_reg::instance().get(id1); // {"FOO", "protein_coding"}
```

This pattern avoids overloading `gene_info::operator==` and `std::hash<gene_info>` to consider only `gene_id` — which would leak partial equality to every consumer that holds the payload outside the registry.

**Key points:**

- **Two-argument `intern(key, payload)`** is the primary form when `Payload != Key`. The single-arg `intern(value)` is still available, but only when `Key == Payload` (enforced by a `requires` clause).
- **First-write-wins on payload.** Re-interning a key that is already present returns the existing ID and silently drops the new payload. Matches the typical "first source carries the canonical record; later sources may carry placeholder fields" pattern (e.g. annotations sorted first, downstream entries reusing the ID).
- **`find(key)` and `get(id)`** signatures use `Key` and `Payload` respectively: `find(const Key&) -> std::optional<id_type>`, `get(id_type) -> const Payload&`.

The tagged form reads naturally when both `Tag` and `Payload` are explicit:

```cpp
using gene_reg = gdt::registry<std::string, gene_tag, gene_info>;
```

## The `registry_value` Concept

`registry<Key, ...>` constrains `Key` with the `registry_value` concept, which requires `Key` to be:

- **Equality-comparable** (`std::equality_comparable`) — used to detect existing entries.
- **Hashable** via `std::hash<Key>` — used by the internal key→ID lookup.

(`Payload` has no concept requirement of its own. The serialization methods additionally need both `serializer<Key>` and `serializer<Payload>` to be available — see [Serialization](#serialization-and-deserialization).)

Built-in types like `std::string`, `int`, and trivial wrappers satisfy this out of the box. Custom types need both `operator==` and a `std::hash` specialization:

```cpp
struct SampleInfo {
    std::string name;
    std::string tissue;
    int replicate;

    bool operator==(const SampleInfo& other) const {
        return name == other.name
            && tissue == other.tissue
            && replicate == other.replicate;
    }
};

template <>
struct std::hash<SampleInfo> {
    size_t operator()(const SampleInfo& s) const noexcept {
        size_t h1 = std::hash<std::string>{}(s.name);
        size_t h2 = std::hash<std::string>{}(s.tissue);
        size_t h3 = std::hash<int>{}(s.replicate);
        return h1 ^ (h2 << 1) ^ (h3 << 2);
    }
};

auto& reg = gdt::registry<SampleInfo>::instance();
auto id = reg.intern(SampleInfo{"sample1", "liver", 1});
```

Without these, the registry will fail to compile with a clear `registry_value` constraint error.

## Thread Safety

`registry<T>` is safe to use concurrently:

- **Lock-protected:** `intern()`, `find()`, `clear()`, `serialize()`, `deserialize()` acquire an internal `std::mutex`.
- **Unlocked fast paths:** `get(id)`, `contains(id)`, `size()`, `empty()`.

`get(id)` is safe to call concurrently with `intern()` as long as `id` was obtained from an `intern()` call that **happens-before** the `get()` (the natural pattern: one thread interns and publishes the returned ID via a queue, atomic, or thread join, and another thread then reads it). `size()`, `empty()`, and `contains()` return best-effort snapshots under concurrent writes.

## Why Dedup-on-Insert?

Calling `intern(x)` is idempotent: `intern(x) == intern(x)` for all `x`. This means callers don't have to maintain their own value→ID map — the registry collapses N references to the same value down to a single ID slot:

```cpp
auto& reg = gdt::registry<std::string>::instance();

// 10,000 BED entries on chr1 → only one registry slot
for (const auto& entry : reader) {
    auto chrom_id = reg.intern(entry.chrom);
    grove.insert_data(entry.chrom, interval{...}, chrom_id);
}

// reg.size() is the number of distinct chromosomes, not the number of entries.
```

## Serialization and Deserialization

`registry::serialize()` and `registry::deserialize()` persist the registry's contents to and from a binary stream.

### Wire format

The serialized layout depends on whether `Key` and `Payload` are the same type:

- **`Key == Payload`** (the default): `uint64_t count` followed by each payload via `serializer<Payload>`. This matches the historical format — **old `.gg` files still load**.
- **`Key != Payload`**: `uint64_t count` followed by `(key, payload)` pairs in ID order. Requires both `serializer<Key>` and `serializer<Payload>` to be available.

### Failure semantics

- **Strong exception guarantee on `deserialize()`.** Reads build into local containers; the singleton is committed via a noexcept move-assign only after the read loop completes. If anything throws partway through (truncated stream, `serializer::read` failure, key/payload ctor failure), the singleton is left **exactly as it was before the call**. Callers can safely retry, fall back, or bail.
- **Count validation.** A header count greater than the `id_type` capacity is rejected before any read attempts with `std::runtime_error("Failed to deserialize registry: entry count exceeds id_type capacity")`. This protects against pathological allocations on attacker-crafted or malformed streams.
- **Duplicate-key rejection.** A stream containing two entries with the same key is rejected with `std::runtime_error("Failed to deserialize registry: duplicate key")`. Legitimate `serialize()` output never trips this check (since `intern()` deduplicates) — it matters only for hand-crafted or corrupted streams.

### Concurrency note

The slow read loop in `deserialize()` runs **without holding the registry mutex**; only the brief commit step is locked. As a result, concurrent `intern()`/`find()`/`get()` calls on the singleton are not blocked by ongoing deserialization.

## Registry Features

- `instance()`: Get the singleton registry for a given `(Key, Tag, Payload)` triple
- `intern(key, payload)`: Intern a `(key, payload)` pair; returns the existing ID and silently drops `payload` if `key` is already present (first-write-wins, `[[nodiscard]]`)
- `intern(value)`: Single-arg form — only available when `Key == Payload` (the default)
- `find(key)`: Look up a key without inserting; returns `std::optional<id_type>`
- `get(id)`: Retrieve a payload by ID (returns `const Payload&`, throws `std::out_of_range` on invalid ID)
- `contains(id)`: Check if an ID is valid
- `size()`, `empty()`: Query registry state
- `clear()`, `reset()`: Clear all data (invalidates all IDs)
- `serialize(os)`, `deserialize(is)`: Persist and restore registry data (see [Serialization](#serialization-and-deserialization) for failure semantics and wire format)
- `null_id`: Sentinel value representing an invalid/unset ID
- `key_is_payload`: `static constexpr bool`, true iff `Key == Payload`

Each `(Key, Tag, Payload)` triple gets its own independent singleton with its own ID space.