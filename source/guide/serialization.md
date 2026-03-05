# Serialization

Genogrove supports serialization for persisting groves to disk and loading them back. This avoids
re-parsing and re-inserting data from source files, which is significantly faster for large datasets.

## Basic Usage

Save a grove to disk and load it back:

```cpp
#include <genogrove/structure/grove/grove.hpp>
#include <genogrove/data_type/interval.hpp>
#include <fstream>

namespace gdt = genogrove::data_type;
namespace gst = genogrove::structure;

int main() {
    gst::grove<gdt::interval, std::string> my_grove(100);
    my_grove.insert_data("chr1", gdt::interval{100, 200}, "gene1");
    my_grove.insert_data("chr1", gdt::interval{300, 400}, "gene2");

    // Save to disk
    {
        std::ofstream out("grove.bin", std::ios::binary);
        my_grove.serialize(out);
    }

    // Load from disk
    {
        std::ifstream in("grove.bin", std::ios::binary);
        auto loaded = gst::grove<gdt::interval, std::string>::deserialize(in);
        // loaded is a fully functional grove with all data restored
    }

    return 0;
}
```

Always open streams with `std::ios::binary` to avoid platform-specific newline translation.

## How It Works

The grove serializes its complete B+ tree structure to a stream in a depth-first traversal:

1. Tree order and number of indices (chromosomes)
2. For each index: the index name followed by the full tree (nodes, keys, and associated data)
3. External key storage

All built-in key types (`interval`, `genomic_coordinate`, `numeric`, `kmer`) and common data types
(`std::string`, trivially copyable types like `int`, `double`, `uint32_t`) are serialized automatically.

## Combined Persistence with Data Registry

When using `data_registry` to store shared metadata (e.g., sample names referenced by ID in the grove),
serialize the registry **before** the grove and deserialize in the same order:

```cpp
#include <genogrove/data_type/data_registry.hpp>
#include <fstream>

namespace gdt = genogrove::data_type;
namespace gst = genogrove::structure;

int main() {
    auto& registry = gdt::data_registry<std::string>::instance();
    gst::grove<gdt::interval, uint32_t> my_grove(100);

    // Register shared metadata, store IDs in the grove
    auto id1 = registry.register_data("SampleA_liver");
    auto id2 = registry.register_data("SampleB_brain");
    my_grove.insert_data("chr1", gdt::interval{100, 200}, id1);
    my_grove.insert_data("chr1", gdt::interval{150, 250}, id2);

    // Save: registry first, then grove
    {
        std::ofstream out("data.bin", std::ios::binary);
        registry.serialize(out);
        my_grove.serialize(out);
    }

    // Load: same order
    registry.clear();
    {
        std::ifstream in("data.bin", std::ios::binary);
        auto& restored = gdt::data_registry<std::string>::deserialize(in);
        auto loaded = gst::grove<gdt::interval, uint32_t>::deserialize(in);

        // Registry IDs in the grove still resolve correctly
        auto results = loaded.intersect(gdt::interval{100, 200}, "chr1");
        for (auto* key : results.get_keys()) {
            auto* name = restored.get(key->get_data());  // "SampleA_liver"
        }
    }

    return 0;
}
```

## Custom Key Type Serialization

If you use a custom key type with the grove, it must implement a `serialize` member method and a
static `deserialize` factory method:

```cpp
struct CustomInterval {
    size_t start;
    size_t end;

    void serialize(std::ostream& os) const {
        os.write(reinterpret_cast<const char*>(&start), sizeof(start));
        os.write(reinterpret_cast<const char*>(&end), sizeof(end));
    }

    [[nodiscard]] static CustomInterval deserialize(std::istream& is) {
        CustomInterval ci;
        is.read(reinterpret_cast<char*>(&ci.start), sizeof(ci.start));
        is.read(reinterpret_cast<char*>(&ci.end), sizeof(ci.end));
        if (!is) throw std::runtime_error("Failed to deserialize CustomInterval");
        return ci;
    }

    // ... other key_type_base requirements (operator<, overlap, aggregate, etc.)
};
```

## Custom Data Type Serialization

For custom data types stored as associated data in keys, you have two options:

### Option 1: Member methods

Add `serialize` and `deserialize` methods directly to your type:

```cpp
struct Annotation {
    std::string name;
    double score;

    void serialize(std::ostream& os) const {
        genogrove::data_type::serializer<std::string>::write(os, name);
        os.write(reinterpret_cast<const char*>(&score), sizeof(score));
    }

    [[nodiscard]] static Annotation deserialize(std::istream& is) {
        auto name = genogrove::data_type::serializer<std::string>::read(is);
        double score;
        is.read(reinterpret_cast<char*>(&score), sizeof(score));
        if (!is) throw std::runtime_error("Failed to deserialize Annotation");
        return {std::move(name), score};
    }
};
```

### Option 2: Specialize serialization_traits

For third-party types you cannot modify, specialize `serialization_traits`:

```cpp
#include <genogrove/data_type/serialization_traits.hpp>

template<>
struct genogrove::data_type::serialization_traits<ThirdPartyType> {
    static void serialize(std::ostream& os, const ThirdPartyType& value) {
        // write fields to os
    }

    static ThirdPartyType deserialize(std::istream& is) {
        // read fields from is and return constructed object
    }
};
```

### What works automatically

- **Trivially copyable types** (`int`, `double`, `uint32_t`, etc.) — serialized via `memcpy`
- **`std::string`** — built-in specialization (length-prefixed)
- **Built-in key types** (`interval`, `genomic_coordinate`, `numeric`, `kmer`) — member methods provided

## Important Notes

- All `deserialize` methods (`node::deserialize`, `grove::deserialize`, `data_registry::deserialize`, `serialization_traits<std::string>::deserialize`) throw `std::runtime_error` on corrupt or truncated streams
- `node::deserialize` additionally validates B+ tree invariants (num_keys < order, num_children <= order)
- The grove's `fill_factor` is included in the serialized format and restored on deserialize
- Graph edges are **not** serialized — you must rebuild the graph overlay after deserialization
- All `deserialize` methods are marked `[[nodiscard]]` to prevent accidentally discarding the result
