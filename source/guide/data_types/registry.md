# Registry

The `registry<T>` is a per-type singleton that **interns** values: every distinct value gets one stable 4-byte ID, and asking to intern the same value again returns the existing ID. This is useful for collapsing many references to the same value (chromosome names, transcript/gene IDs, sample identifiers seen thousands of times across grove entries) down to a single ID that can be stored alongside grove keys.

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

## The `registry_value` Concept

`registry<T>` constrains `T` with the `registry_value` concept, which requires `T` to be:

- **Equality-comparable** (`std::equality_comparable`) — used to detect existing entries.
- **Hashable** via `std::hash<T>` — used by the internal value→ID lookup.

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

## Registry Features

- `instance()`: Get the singleton registry for a given type
- `intern(value)`: Intern a value and return its stable ID; returns the existing ID if already interned (dedup-on-insert, `[[nodiscard]]`)
- `find(value)`: Look up a value without inserting; returns `std::optional<id_type>`
- `get(id)`: Retrieve a value by ID (returns `const T&`, throws `std::out_of_range` on invalid ID)
- `contains(id)`: Check if an ID is valid
- `size()`, `empty()`: Query registry state
- `clear()`, `reset()`: Clear all data (invalidates all IDs)
- `serialize(os)`, `deserialize(is)`: Persist and restore registry data
- `null_id`: Sentinel value representing an invalid/unset ID

Each type `T` gets its own independent singleton registry with its own ID space.