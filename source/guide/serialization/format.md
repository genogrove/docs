# The `.gg` Format

This page describes what a {term}`serialized <serialization>` {term}`grove` looks like on disk,
which {term}`versions of the format <format version>` exist, the extra header the {term}`CLI` writes
in front of the grove, and the text export for graph visualisation.
You do not need any of it to save and load a grove; read it when you need to tell whether a file is
compatible, when you want to read a CLI-built index from your own code, or when you are curious how
{doc}`partial reading <partial_reading>` is possible.

## How it works

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

A `.gg` is a short plain header followed by many small blocks. Each block is compressed on its own
with {term}`zlib`, so a reader can inflate (decompress) one block without touching the others. That
is what makes partial reading possible. There is one block for each {term}`B+ tree` {term}`node`.
The {term}`external keys <external key>` (keys that are not stored in a tree node) go into
fixed-size blocks of at most 512 keys, so their block count grows with the number of external keys.
The output is a compressed binary {term}`stream`, so you cannot read it in a hex editor.

Each block has a length in front of it. A block is inflated from a buffer of exactly that length, so
the source is read from start to end. For this reason `grove::deserialize` works on non-{term}`seekable`
input streams and leaves any bytes after the grove unread.

The stream is laid out as:

1. A plain (uncompressed) header: {term}`magic`, tree {term}`order`, the index directory (one name +
   root block id per chromosome) and the block/key counts
2. One zlib-compressed block per B+ tree node, in depth-first order per index. A leaf block holds
   all its keys and payloads first, then the id of the next leaf. After that it holds the edge lists
   of every key, key by key: the **outgoing** list and then the **incoming** list (other endpoint as
   `(block_id, slot)`, plus metadata when `edge_data_type != void`). An internal node block holds
   its keys and the number of children, and no edge lists
3. External-key blocks. Each block holds a key count, then all its keys and payloads, then the
   outgoing and incoming edge lists of every key, in the same form as in a leaf block

Every edge therefore appears twice on disk — under its source and under its target — which is what
lets `grove_view` surface either side of an edge after paging in only one endpoint's block.

::::

::::{tab-item} {{ py_tab }}
:sync: py

A `.gg` is a short plain header followed by many small blocks. Each block is compressed on its own
with {term}`zlib`, so `GroveView` can inflate (decompress) just the blocks a query needs. There is
one block for each {term}`B+ tree` {term}`node`. The {term}`external keys <external key>` go into
fixed-size blocks of at most 512 keys, so their block count grows with the number of external keys.
A file written by `serialize()` is byte for byte the stream the C++ library writes; pygenogrove adds
nothing of its own.

The stream is laid out as:

1. A plain (uncompressed) header: {term}`magic`, tree {term}`order`, the index directory (one name +
   root block id per chromosome) and the block/key counts
2. One zlib-compressed block per B+ tree node, in depth-first order per index. A leaf block holds
   all its keys and payloads first, then the id of the next leaf. After that it holds the edge lists
   of every key, key by key: the **outgoing** list and then the **incoming** list (other endpoint as
   `(block_id, slot)`, plus metadata on the edge-carrying `Grove` / `NumericGrove` / `KmerGrove`).
   An internal node block holds its keys and the number of children, and no edge lists
3. External-key blocks. Each block holds a key count, then all its keys and payloads, then the
   outgoing and incoming edge lists of every key, in the same form as in a leaf block

The only Python-specific detail is that payloads and edge metadata of the universal `Grove` are
stored as JSON text. Every edge appears twice on disk — under its source and under its target —
which is what lets `GroveView` follow an edge from either end after paging in only one endpoint's
block.

::::

:::::

## Format versions and compatibility

The stream format is versioned as `format_major.format_minor` (the numbers appear in the
[`.gg` file header](#the-gg-file-header) the CLI writes). The current format is **0.3**.

| Format | genogrove | Payload |
|---|---|---|
| 0.1 | < 0.25.0 | Whole file a single zlib stream |
| 0.2 | 0.25.0 – 0.26.0 | Block-structured (per-node blocks, external-key chunks); edges recorded under their source only |
| 0.3 | 0.26.1+ | Block-structured; each key records its outgoing **and** incoming edge lists, enabling reverse traversal in a view |

:::{warning}
**No serialization back-compat.** A build reads exactly one format: v0.26.1+ rejects 0.1 and 0.2
`.gg` files, which must be regenerated (re-run {doc}`genogrove idx </cli>` or save the grove again).
While `format_major == 0` the format is still evolving and may break again.
:::

:::{warning}
**Build the index again if you inserted unsorted data with genogrove 0.25.5 or older.** Those
releases put out-of-order inserts in the wrong place in trees deeper than two levels, so
`intersect()` never returned some keys. Version 0.25.6 fixed this, but the fix does **not** repair a
file that already exists: an affected `.gg` loads as before. Build such an index again from the
source data, or keep using the genogrove version that wrote it. To see which version you have, run
`genogrove --version`, or `python -c "import pygenogrove; print(pygenogrove.__genogrove_version__)"`
for the genogrove version inside pygenogrove.
:::

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

The public signatures — `serialize(std::ostream&)` / `deserialize(std::istream&)` — have not
changed across these versions. A stream of the wrong format fails in `deserialize` with
`std::runtime_error` (`"Failed to deserialize grove: bad magic (not a format 0.3 grove stream)"`
on the current build).

::::

::::{tab-item} {{ py_tab }}
:sync: py

`serialize(path)` / `Grove.deserialize(path)` have not changed across these versions. pygenogrove
0.8.0 and later write and read format 0.3; a file of an older format fails in `deserialize` with
`RuntimeError`.

::::

:::::

## The `.gg` file header

Every `.gg` file produced by the {doc}`CLI </cli>`'s `idx` subcommand begins with a **12-byte plain
(uncompressed) header** written before the grove stream. Because it is uncompressed, a `.gg` file
can be identified and validated without decompressing first. In a terminal, `xxd -l 12 index.gg`
prints the twelve header bytes with the letters `GROV` visible on the right. The `isec -i` subcommand validates this header before
reading the grove. A file written by `serialize` directly has **no** such header.

| Offset | Size | Field | Notes |
|---|---|---|---|
| 0 | 4 | `magic` = `"GROV"` | inspectable via `xxd` |
| 4 | 1 | `format_major` = 0 | pre-1.0; any change may break compatibility |
| 5 | 1 | `format_minor` = 3 | see [Format versions](#format-versions-and-compatibility) |
| 6 | 1 | `lib_major` | informational |
| 7 | 1 | `lib_minor` | informational |
| 8 | 1 | `lib_patch` | informational |
| 9 | 1 | `payload_type` | `0x01` = BED, `0x02` = GFF |
| 10 | 2 | `reserved` | zero |

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

The header API lives in `genogrove::io` and is declared in `genogrove/io/gg_format.hpp` as:

```cpp
enum class gg_payload_type : uint8_t { BED = 0x01, GFF = 0x02 };

struct gg_header {
    static constexpr std::size_t SIZE = 12;
    uint8_t format_major, format_minor;
    uint8_t lib_major, lib_minor, lib_patch;
    gg_payload_type payload_type;
};
```

Methods:

- `static gg_header current(gg_payload_type payload_type)` — a header stamped with the current
  library version and the given payload type; use it on the writer side
- `void write(std::ostream& os) const` — write the 12 bytes
- `static gg_header read(std::istream& is)` — read and validate; throws `std::runtime_error` on a
  bad magic value, an unsupported `(format_major, format_minor)` pair, or an unknown `payload_type`.
  Library-version differences (`lib_*`) are **informational only** and never cause rejection

The example below needs an `index.gg` from the CLI. Build it in a terminal with
`genogrove idx features.bed -o index.gg` (see the {doc}`CLI page </cli>`). To read a CLI-built
index from your own code, read the header first and then the grove from the same stream, or open a
`grove_view` with `data_offset = gio::gg_header::SIZE`:

```cpp
#include <genogrove/io/gg_format.hpp>
#include <genogrove/io/bed_reader.hpp>
#include <genogrove/structure/grove/grove.hpp>
#include <fstream>

namespace gdt = genogrove::data_type;
namespace gio = genogrove::io;
namespace gst = genogrove::structure;

std::ifstream in("index.gg", std::ios::binary);
const auto header = gio::gg_header::read(in);          // validates, leaves `in` at the grove
if (header.payload_type == gio::gg_payload_type::BED) {
    auto g = gst::grove<gdt::interval, gio::bed_entry, std::string>::deserialize(in);
}
```

The CLI's indexes use `grove<interval, bed_entry, std::string>` (or `gff_entry` for GFF input) —
a `std::string` edge type — so that `idx --links` can attach
[per-edge metadata](../../cli.md#links-attaching-graph-edges). CLI-built indexes from before v0.25.0
used a `void` edge type, and files written before this header existed have no header. Both kinds
no longer load; build them again, as the warning above says.

::::

::::{tab-item} {{ py_tab }}
:sync: py

pygenogrove has no header API, and **a CLI-built index cannot currently be read from Python**.
`Grove.deserialize()` expects a bare grove stream, and although `GroveView.open()` can skip the
header with `data_offset=12`, the CLI saves its keys and edge labels in a different form than the
Python views expect (the CLI uses the C++ `interval` key and text edge labels; `BedGroveView` and
`GffGroveView` expect `GenomicCoordinate` keys and edges with no label). The file does not record
its types, so such an open reads the blocks wrongly instead of failing with an error. Views bound to the CLI's types are requested in
[pygenogrove#117](https://github.com/genogrove/pygenogrove/issues/117), and a type check in the
stream in [genogrove#593](https://github.com/genogrove/genogrove/issues/593).

Until then, build the index from Python and read it with the matching view. The example needs a
BED file called `features.bed` in the current directory (any BED file with `chr1` records works):

```python
import pygenogrove as pg

g = pg.BedGrove(100)
g.insert_bulk("chr1", [e for e in pg.BedReader("features.bed") if e.chrom == "chr1"])
g.serialize("features.gg")

view = pg.BedGroveView.open("features.gg")
```

The header back-compat warning on the C++ tab does not affect Python files: `serialize()` never
wrote a header, so no pygenogrove file is invalidated by it.

::::

:::::

## SIF export (visualisation)

A grove can be exported as **{term}`SIF`** (Simple Interaction Format) text for visualisation in
tools such as Cytoscape (a network-visualisation program). The output is tab-separated and uses
three interaction types: `nodelink` (internal node → child), `leaflink` (leaf → next leaf) and
`keylink` (key → {term}`graph overlay` neighbour). An empty grove produces no output.

:::{warning}
The chromosomes may come out in a different order each time the program runs: index iteration
order is **not stable across runs**, because the grove keeps its indexes in a hash map, which has no
fixed iteration order. Treat the output as a *set* of interactions rather than an ordered list.
:::

To look at the graph, open Cytoscape and choose *File → Import → Network from File*, then pick the
`.sif` file.

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

Two {term}`const` {term}`overloads <overload>` are available:

```cpp
// Whole-grove export: walks the grove's own roots, no node pointer needed.
void grove_to_sif(std::ostream& os) const;

// Per-tree primitive: visualize a single tree given its root node.
void grove_to_sif(std::ostream& os, const node<key_type, data_type>* root) const;
```

Both are stream-only by design, mirroring `serialize()` / `deserialize()` — there is intentionally
**no** path overload, so wrap your own `std::ofstream`. With `my_grove` from the
{doc}`saving example <index>`:

```cpp
#include <fstream>

std::ofstream out("grove.sif");
my_grove.grove_to_sif(out);   // writes every indexed tree
```

::::

::::{tab-item} {{ py_tab }}
:sync: py

`to_sif(path)` writes the whole grove to a file and is available on every grove class. It
{term}`releases the GIL <GIL>`. There is no per-tree variant. With `g` from the
{doc}`saving example <index>`:

```python
g.to_sif("grove.sif")
```

::::

:::::