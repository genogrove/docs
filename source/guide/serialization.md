# Serialization

Genogrove supports serialization for persisting groves to disk and loading them back. This avoids
re-parsing and re-inserting data from source files, which is significantly faster for large datasets.

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

### Basic Usage

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

`grove::serialize()` (and the supporting `grove_to_sif()` and `node::serialize()`) are
**`const`-qualified**, so consumers holding a `const grove&` — for example a read-only post-build
query layer — can serialize without a `const_cast`:

```cpp
void persist(const gst::grove<gdt::interval, std::string>& g, std::ostream& os) {
    g.serialize(os);   // OK — serialize() is const
}
```

### How It Works

The grove serializes its complete B+ tree structure using **zlib compression**. The output is a
compressed binary stream (not raw bytes), so files are compact but not directly inspectable with
hex editors. Internally the data is written in a depth-first traversal:

1. Tree order and number of indices (chromosomes)
2. For each index: the index name followed by the full tree (nodes, keys, and associated data)
3. External key storage
4. Graph overlay edges

All built-in key types (`interval`, `genomic_coordinate`, `numeric`, `kmer`) and common data types
(`std::string`, trivially copyable types like `int`, `double`, `uint32_t`) are serialized automatically.

### Combined Persistence with Registry

When using `registry` to store shared metadata (e.g., sample names referenced by ID in the grove),
serialize the registry **before** the grove and deserialize in the same order:

```cpp
#include <genogrove/data_type/registry.hpp>
#include <fstream>

namespace gdt = genogrove::data_type;
namespace gst = genogrove::structure;

int main() {
    auto& reg = gdt::registry<std::string>::instance();
    gst::grove<gdt::interval, uint32_t> my_grove(100);

    // Intern shared metadata, store IDs in the grove
    auto id1 = reg.intern("SampleA_liver");
    auto id2 = reg.intern("SampleB_brain");
    my_grove.insert_data("chr1", gdt::interval{100, 200}, id1);
    my_grove.insert_data("chr1", gdt::interval{150, 250}, id2);

    // Save: registry first, then grove
    {
        std::ofstream out("data.bin", std::ios::binary);
        reg.serialize(out);
        my_grove.serialize(out);
    }

    // Load: same order
    reg.clear();
    {
        std::ifstream in("data.bin", std::ios::binary);
        auto& restored = gdt::registry<std::string>::deserialize(in);
        auto loaded = gst::grove<gdt::interval, uint32_t>::deserialize(in);

        // Registry IDs in the grove still resolve correctly
        auto results = loaded.intersect(gdt::interval{100, 200}, "chr1");
        for (auto* key : results.get_keys()) {
            const auto& name = restored.get(key->get_data());  // "SampleA_liver"
        }
    }

    return 0;
}
```

### Custom Key Type Serialization

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

### Custom Data Type Serialization

For custom data types stored as associated data in keys, you have two options:

#### Option 1: Member methods

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

#### Option 2: Specialize serialization_traits

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

#### What works automatically

- **Trivially copyable types** (`int`, `double`, `uint32_t`, etc.) — serialized via `memcpy`
- **`std::string`** — built-in specialization (length-prefixed)
- **Built-in key types** (`interval`, `genomic_coordinate`, `numeric`, `kmer`) — member methods provided
- **`gio::bed_entry`** (with its nested `gio::block_info`) — member `serialize`/`deserialize`
  provided, so a `grove<gdt::interval, gio::bed_entry>` can be persisted directly. The `.gg`
  files produced by the `idx` CLI subcommand are this form. `gio::rgb_color` and `gio::thick_info`
  are trivially copyable and serialize automatically.

### Source Stream Must Be Seekable for Concatenated Payloads

`grove::deserialize()` uses zlib's streaming decoder, which may finish consuming the compressed
payload before exhausting the input buffer. To preserve any bytes that follow the grove (e.g.,
concatenated payloads, sentinel markers, file tails), the internal `inflate_streambuf` rewinds
the unconsumed bytes via `source.seekg(...)`.

**The source stream must therefore be seekable when anything follows the grove in the stream.**
On non-seekable sources (pipes, sockets, custom non-seekable streambufs) the seek fails and
`deserialize()` throws:

> `inflate_streambuf: source stream is not seekable; concatenated payloads require a seekable source`

For a single-payload `.gg` file loaded via `std::ifstream`, this requirement is automatically
satisfied — file streams are seekable. The requirement matters only for the concatenated-payload
pattern (registry then grove from the same stream, multiple grove payloads back-to-back, sentinel
trailers).

If you must deserialize from a non-seekable source, copy it into a `std::stringstream` first:

```cpp
std::stringstream buf;
buf << non_seekable_source.rdbuf();        // drain into a seekable buffer
auto g = gst::grove<...>::deserialize(buf);
```

### Important Notes

- `grove::deserialize()` returns a grove **by value**. Because `grove` is a move-only type (copy is deleted), the return relies on Named Return Value Optimization (NRVO) or implicit move. No special handling is needed—just assign the result to a local variable as shown in the examples above.
- All `deserialize` methods (`node::deserialize`, `grove::deserialize`, `registry::deserialize`, `serialization_traits<std::string>::deserialize`) throw `std::runtime_error` on corrupt or truncated streams.
- `node::deserialize` additionally validates B+ tree invariants (num_keys < order, num_children <= order).
- `registry::deserialize` provides a **strong exception guarantee**: if the stream throws or is truncated, the singleton is left exactly as it was before the call. The new state is built into local containers and committed via noexcept move-assign only after the read loop completes. It also rejects header counts that exceed the `id_type` capacity (`"Failed to deserialize registry: entry count exceeds id_type capacity"`) and streams containing duplicate keys (`"Failed to deserialize registry: duplicate key"`). See {doc}`data_types/registry` for details.
- Graph edges added via `add_edge()` or `link_if()` are now persisted during serialization and restored on deserialize.
- **Breaking format change**: The serialized format now includes graph edges after external keys. Files serialized with older versions are incompatible and must be re-created.
- All `deserialize` methods are marked `[[nodiscard]]` to prevent accidentally discarding the result.

### The `.gg` File Header

Every `.gg` file produced by the `idx` CLI subcommand begins with a **12-byte plain (uncompressed)
header** written before the zlib-compressed grove payload. Because it is uncompressed, a `.gg` file
can be identified and validated without decompressing first (e.g. with `xxd` or `file`). The
`intersect -i` (`isec`) subcommand validates this header before deserializing.

The on-disk layout is:

| Offset | Size | Field | Notes |
|---|---|---|---|
| 0 | 4 | `magic` = `"GROV"` | inspectable via `xxd` / `file` |
| 4 | 1 | `format_major` = 0 | pre-1.0; any change may break compatibility |
| 5 | 1 | `format_minor` = 1 | starts at 0.1 |
| 6 | 1 | `lib_major` | informational |
| 7 | 1 | `lib_minor` | informational |
| 8 | 1 | `lib_patch` | informational |
| 9 | 1 | `payload_type` | `0x01` = BED, `0x02` = GFF |
| 10 | 2 | `reserved` | zero |

The API lives in `genogrove::io`:

```cpp
#include <genogrove/io/gg_format.hpp>

namespace gio = genogrove::io;

enum class gg_payload_type : uint8_t { BED = 0x01, GFF = 0x02 };

struct gg_header {
    [[nodiscard]] static gg_header current(gg_payload_type payload_type);  // writer-side factory
    void write(std::ostream& os) const;                                    // write the 12 bytes
    [[nodiscard]] static gg_header read(std::istream& is);                 // read + validate
};
```

- `gg_header::current(payload_type)` builds a header stamped with the current library version and
  the given payload type — use it on the writer side.
- `write(std::ostream&)` writes the 12-byte header.
- `gg_header::read(std::istream&)` reads and validates the header. It throws `std::runtime_error`
  on a bad magic value, an unsupported `(format_major, format_minor)` pair, or an unknown
  `payload_type`. Library-version differences (`lib_major`/`lib_minor`/`lib_patch`) are
  **informational only** and never cause rejection.

:::{warning}
**No backwards compatibility.** Pre-existing `.gg` files written before this header was added no
longer parse and must be re-indexed. This is consistent with the project's
no-backwards-compatibility-for-serialization policy.
:::

### SIF Export (visualization)

The grove can be exported to **SIF** (Simple Interaction Format) text for visualization in tools
such as Cytoscape. Two overloads are available:

```cpp
// Whole-grove export: walks the grove's own roots, no node pointer needed.
void grove_to_sif(std::ostream& os) const;

// Per-tree primitive: visualize a single tree given its root node.
void grove_to_sif(std::ostream& os, const node<key_type, data_type>* root) const;
```

The node-less overload exports the **entire grove** (all indexed trees) in one call. An empty grove
produces no output. Both overloads are stream-only by design (mirroring `serialize()` /
`deserialize()`) — there is intentionally **no** `to_sif(path)` overload, so callers wrap their own
`std::ofstream`:

```cpp
#include <fstream>

std::ofstream out("grove.sif");
my_grove.grove_to_sif(out);   // writes every indexed tree
```

The per-tree overload (`grove_to_sif(os, root)`) remains available for visualizing a single tree.

The output is tab-separated and uses three interaction types: `nodelink` (internal node → child),
`leaflink` (leaf → next leaf), and `keylink` (key → graph-overlay neighbour).

:::{warning}
Index iteration order is **not stable across runs** (hash-map iteration) — treat the output as a
*set* of interactions rather than an ordered list.
:::

::::

::::{tab-item} {{ py_tab }}
:sync: py

### Serialization

Groves persist to a zlib-compressed `.gg` binary.

- `grove.serialize(path)` — write the grove (keys + payloads + graph overlay) to `path`. Releases the GIL.
- `Grove.deserialize(path) -> Grove` (static) — load a grove written by `serialize`. Releases the GIL.

```python
g.serialize("out.gg")
reloaded = pg.Grove.deserialize("out.gg")
```

Note the C++ interop: an edgeless universal-`Grove` `.gg` stores its payload as JSON text, readable
by a C++ `grove<genomic_coordinate, std::string>`; with labelled edges the interop type is
`grove<genomic_coordinate, std::string, std::string>`. Typed `BedGrove` / `GffGrove` `.gg` files
round-trip the structured `BedEntry` / `GffEntry` payloads.

### SIF export (visualization)

`grove.to_sif(path)` writes the grove to a **SIF** (Simple Interaction Format) text file for
Cytoscape — available on every grove. Tab-separated interactions: `nodelink` (node → child),
`leaflink` (leaf → next leaf), `keylink` (key → graph-overlay neighbour). An empty grove writes an
empty file. Releases the GIL.

:::{warning}
Line and index order are **not stable across runs** (hash-map iteration) — treat the output as a
*set* of interactions.
:::

```python
g.to_sif("graph.sif")
```

::::

:::::