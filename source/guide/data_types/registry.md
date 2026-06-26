# Registry

A **registry** interns values: every distinct key gets one stable 4-byte ID, and
interning the same key again returns the existing ID. This collapses many
references to the same value (chromosome names, transcript/gene IDs, sample
identifiers seen thousands of times) down to a single ID stored alongside grove
keys.

:::::{tab-set}

::::{tab-item} C++

The `registry<Key, Tag, Payload>` is a per-type singleton.

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

### Tagged Singletons

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

### Storing Richer Payloads

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
- **First-write-wins on payload.** Re-interning a key that is already present returns the existing ID and silently drops the new payload.
- **`find(key)` and `get(id)`** signatures use `Key` and `Payload` respectively: `find(const Key&) -> std::optional<id_type>`, `get(id_type) -> const Payload&`.

### The `registry_value` Concept

`registry<Key, ...>` constrains `Key` with the `registry_value` concept, which requires `Key` to be **equality-comparable** (`std::equality_comparable`) and **hashable** via `std::hash<Key>`. Built-in types like `std::string` and `int` satisfy this out of the box; custom types need both `operator==` and a `std::hash` specialization.

### Thread Safety

`registry<T>` is safe to use concurrently:

- **Lock-protected:** `intern()`, `find()`, `clear()`, `serialize()`, `deserialize()` acquire an internal `std::mutex`.
- **Unlocked fast paths:** `get(id)`, `contains(id)`, `size()`, `empty()`.

`get(id)` is safe to call concurrently with `intern()` as long as `id` was obtained from an `intern()` call that **happens-before** the `get()`. `size()`, `empty()`, and `contains()` return best-effort snapshots under concurrent writes.

### Serialization and Deserialization

`registry::serialize()` / `deserialize()` persist the registry to and from a binary stream.

- **Wire format** depends on whether `Key == Payload`: the default stores a `uint64_t count` then each payload (old `.gg` files still load); `Key != Payload` stores `(key, payload)` pairs in ID order.
- **Strong exception guarantee on `deserialize()`** — the singleton is committed only after the read loop completes; a throw mid-stream leaves it exactly as before.
- **Count validation** rejects a header count beyond `id_type` capacity with `std::runtime_error("...entry count exceeds id_type capacity")`.
- **Duplicate-key rejection** with `std::runtime_error("...duplicate key")`; legitimate `serialize()` output never trips this.

### Registry Features

- `instance()`, `intern(key, payload)` / `intern(value)` (`[[nodiscard]]`), `find(key)`, `get(id)`, `contains(id)`, `size()`, `empty()`, `clear()`, `reset()`, `serialize(os)`, `deserialize(is)`, `null_id`, `key_is_payload` (`static constexpr bool`, true iff `Key == Payload`).

::::

::::{tab-item} Python

`Registry` exposes `registry<std::string, void, json_value>` — a process-wide
singleton mapping a **string key** to any JSON-serializable payload (dict / list /
scalar / `None`), deduplicated on the key.

```python
import pygenogrove as pg

r = pg.Registry.instance()

# Plain string interning: get(id) returns the string back
a = r.intern("chr1")          # 0
b = r.intern("chr1")          # 0 (deduplicated -> same id)
r.get(a)                      # "chr1"
r.find("chr2")                # None (lookup without inserting)

# Key -> JSON payload (two-argument form, first-write-wins on the payload)
g = r.intern("ENSG001", {"name": "BRCA2"})
r.get(g)                      # {"name": "BRCA2"}

r.serialize("names.gg")       # round-trips keys AND their JSON payloads
```

**Surface:**

- `Registry.instance()` — the process-wide singleton.
- `intern(value)` — intern a string as its own payload; `get(id)` returns the string.
- `intern(key, payload)` — intern a string key against a JSON payload; dedups on
  the key with **first-write-wins** on the payload.
- `find(key) -> int | None` — lookup without inserting.
- `get(id) -> payload` — raises `IndexError` on an invalid id.
- `contains(id)`, `size()` / `len(r)`, `empty()`, `clear()`, `Registry.reset()`.
- `Registry.null_id` (= `2**32 − 1`).
- `serialize(path)` / `Registry.deserialize(path)` — binary; `deserialize` loads
  into the singleton, **replacing** current data (keys and payloads round-trip).

:::{note}
`Registry` was previously named `StringRegistry`; the rename generalized it from
string-only interning to a string identity mapped to a JSON payload. It is a
**singleton** — one global pool per process; use `reset()` / `clear()` to wipe it
(e.g. between runs or tests). Multiple independent / per-grove registries are not
yet exposed.
:::

::::

:::::