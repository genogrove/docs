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
hex editors. The stream opens with a small plain directory (order, index count, per-index name +
root block id, block counts), then the payload.

**Block-structured payload (format 0.2).** As of genogrove v0.25.0 the payload is
**block-structured**: each B+ tree node is an independently zlib-compressed, length-prefixed block,
and external keys are distributed into fixed-size blocks. (Previously the whole file was a single
zlib stream — format 0.1.) The block structure is what makes random-access partial reading possible
— see [Partial random-access reading](#partial-random-access-reading) below. Because each
block is inflated from an isolated buffer of exactly its length, the source is read sequentially,
so `grove::deserialize` now works on **non-seekable input streams** (pipes, sockets) and leaves any
trailing bytes after the grove intact.

The public signatures (`serialize(std::ostream&)` / `deserialize(std::istream&)`) are unchanged.

```{warning}
**No serialization back-compat.** Format 0.1 `.gg` files are **not readable** by a v0.25.0+ build
and must be regenerated (re-run `genogrove idx` or re-`serialize()`). The header reports
`format_major = 0`, `format_minor = 2`; while `format_major == 0` the format is still evolving and
may break again. See [The `.gg` File Header](#the-gg-file-header).
```

Within a block the data is still written in depth-first order:

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

### Non-Seekable Sources and Concatenated Payloads

As of format 0.2, `grove::deserialize()` reads each block from an isolated buffer of exactly its
length, consuming the source **sequentially**. It no longer needs to rewind, so it works on
**non-seekable sources** (pipes, sockets, custom streambufs) and leaves any bytes that follow the
grove intact — the concatenated-payload pattern (registry then grove from the same stream, multiple
grove payloads back-to-back, sentinel trailers) works without a seekable source.

```{note}
Random-access *partial* reading via [`grove_view`](#partial-random-access-reading) still needs a
seekable source — it seeks to individual block offsets — which is why `grove_view::open` takes a
file path rather than an arbitrary stream. Eager `grove::deserialize` has no such requirement.
```

### Partial random-access reading

`genogrove::structure::grove_view` is a **read-only, partial reader** over a serialized format 0.2
`.gg`. Where `grove::deserialize` eagerly loads the whole file, `grove_view` loads only the blocks a
query walks and caches them for its lifetime. It complements — does not replace — the eager `grove`,
which remains the builder and the load-it-all reader.

```cpp
#include <genogrove/structure/grove/grove_view.hpp>

namespace gst = genogrove::structure;

// Open a .gg for partial reading (seekable source required — takes a path).
auto view = gst::grove_view<gdt::interval, gio::bed_entry, std::string>::open("index.gg");

// Same intersect() signatures/semantics as grove — loads only the O(log n)
// descent path plus overlapping leaves.
auto hits = view.intersect(gdt::interval{100, 200}, "chr1");

// Outgoing graph neighbours; loads only the edge-target block, across chromosomes.
for (auto* k : hits.get_keys()) {
    for (auto* nbr : view.get_neighbors(k)) { /* ... */ }
}
```

**Public surface** (`grove_view<key_type, data_type = void, edge_data_type = void>`):

- `static grove_view open(const std::string& path, std::streamoff data_offset = 0)` — opens a `.gg`,
  reads the directory, and scans the block chain to build a `block_id → file offset` index. Pass
  `data_offset` to start past a leading wrapper (the CLI passes `gg_header::SIZE` to skip the 12-byte
  header). Throws `std::runtime_error` on a missing file, bad magic, a non-seekable/truncated stream,
  or a malformed directory.
- `intersect(const key_type& query, std::string_view index)` and `intersect(const key_type& query)`
  — same signatures and semantics as `grove::intersect` (they share the query engine).
- `get_neighbors(const key* source)` — outgoing graph neighbours, loading only the target block
  (including across chromosomes). `source` must be a key pointer this `grove_view` produced.
- `blocks_loaded()` / `block_count()` — introspection (e.g. to assert a query really was partial).

**Semantics worth calling out:**

- **Non-copyable and non-movable** — it owns the file and a zlib state. Hold it by value from
  `open()`; the return is guaranteed copy elision, so no move is needed.
- **The block cache never evicts** — memory grows with the set of blocks touched, bounded by the
  query footprint.
- **Not thread-safe**, and no `flanking()` yet (eager `grove` only).
- Requires a plain format-0.2 `.gg` written by `grove::serialize`.

The CLI's `isec --in-place` is built on `grove_view` — see the [CLI reference](../cli.md#in-place-querying).

### CLI indexes carry edge metadata

The `.gg` indexes written by the `idx` / `isec` CLI use `grove<interval, {bed,gff}_entry, std::string>`
— a `std::string` graph-edge type — so that `idx --links` can attach [per-edge metadata](../cli.md#links-attaching-graph-edges).
This changed the on-disk format from the earlier `void` edge type: **CLI-built indexes from before
v0.25.0 must be regenerated.** (Consistent with the format-0.2 no-back-compat policy above.)

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
| 5 | 1 | `format_minor` = 2 | 0.2 = block-structured payload (was 0.1, single zlib stream) |
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

### Partial random-access reading with `GroveView`

`GroveView` is a **read-only, partial reader** over a serialized format 0.2 `.gg`. Where
`Grove.deserialize()` loads the whole grove into memory, a `GroveView` reads only the block
directory up front and pages in individual blocks on demand as a query descends the tree, caching
them for the view's lifetime (no eviction). Use it to query a large on-disk index without
materializing it. It complements — does not replace — the eager `Grove`, which stays the builder
and the load-it-all reader.

There is one view class per grove flavour — `GroveView`, `NumericGroveView`, `KmerGroveView`,
`BedGroveView`, `GffGroveView` — each reusing the `Key` / `QueryResult` types of the matching grove.

```python
import pygenogrove as pg

# Open a .gg written by Grove.serialize() (a bare grove stream — data_offset=0).
view = pg.GroveView.open("index.gg")

# Same intersect() signatures/semantics as Grove — loads only the descent path
# plus overlapping leaves. Pass an index name, or omit it to search all indices.
hits = view.intersect(pg.GenomicCoordinate("*", 100, 200), "chr1")

# Outgoing graph neighbours; pages in each target's block on demand, across chromosomes.
for key in hits:
    for nbr in view.get_neighbors(key):
        ...
    view.get_edges(key)                              # edge payloads, parallel to get_neighbors
    view.get_neighbors_if(key, lambda m: m is not None and m["weight"] > 5)  # filtered (universal view only)

# Proof the query was partial: only a subset of blocks was paged in.
assert view.blocks_loaded() < view.block_count()
```

**Surface** (query-only — a view has no `insert()` or `serialize()`):

- `GroveView.open(path, data_offset=0)` *(static)* — open a `.gg` for partial reading. `path` is a
  file written by `Grove.serialize()` (use `data_offset=0`); pass a non-zero `data_offset` only for
  a `.gg` embedded behind a leading header, e.g. a genogrove CLI index. Raises `RuntimeError` on a
  missing file, bad magic, a non-seekable source, or a malformed directory.
- `intersect(query)` / `intersect(query, index)` — same results as the eager `Grove`, loading only
  the blocks the search touches.
- `get_neighbors(key)` — the target keys directly reachable from `key` via graph edges, paging in
  each target's block on demand. `key` must be one this view produced (from `intersect()` or a prior
  `get_neighbors()`). Raises `TypeError` if `key` is `None`.
- `get_edges(source) -> list` — the metadata payloads of `source`'s outgoing edges, in edge order
  (parallel to `get_neighbors(source)`), read from the block already paged in for `source` — no full
  deserialize. Edges added without a payload yield `None`; returns an empty list if `source` has no
  recorded edges. **Edge-carrying views only** (see below).
- `get_neighbors_if(source, predicate) -> list[Key]` — the target keys whose edge metadata satisfies
  `predicate(metadata)`, paging in each surviving target's block on demand exactly like
  `get_neighbors`. The predicate receives the **decoded** payload — which is `None` for an edge added
  without one, so guard for it when mixing labelled and unlabelled edges. Raises `TypeError` if
  `source` is `None`. **Edge-carrying views only** (see below).
- `blocks_loaded()` / `block_count()` — partial-load counters (`block_count()` is `0` for an empty
  grove).

`get_edges` / `get_neighbors_if` exist only on the **universal `GroveView`** (and its point-key
siblings `NumericGroveView` / `KmerGroveView`), whose edges carry a payload. The typed
`BedGroveView` / `GffGroveView` keep unlabelled (void) edges for binary interop, so — mirroring the
mutable `BedGrove` / `GffGrove` — the two labelled-edge reads are absent there; use `get_neighbors`
to traverse. These accessors match the mutable `Grove`'s adjacency surface (see the
{doc}`graph guide </guide/grove/graph>`), but query-only.

:::{warning}
**Not thread-safe.** A query mutates the view's block cache and holds the GIL, so concurrent Python
threads serialize on view I/O — use **one view per thread**. The Keys a view returns point into its
own storage and are valid only while the `GroveView` is alive.
:::

Requires a format 0.2 `.gg` (genogrove v0.25.x). See the C++ tab for the underlying `grove_view`,
and the {doc}`Python API reference </reference/python/grove>` for the full class listing.

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