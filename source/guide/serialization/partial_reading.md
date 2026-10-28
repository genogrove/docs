# Partial Reading

Loading a {term}`.gg file` with {term}`deserialize` reads the whole file into memory. For a large
index that you only want to query a few times, that is wasteful. A **{term}`view`** opens the file,
reads only the small directory at its start, and then pages in just the blocks a query walks — the
path down the {term}`tree <B+ tree>` plus the leaves that overlap — caching them for the view's
lifetime. The result of a query is the same as from the fully loaded {term}`grove`.

A view is **read-only**: it has no insert and no serialize. It complements, rather than replaces,
the {term}`eager` grove, which remains the builder and the load-it-all reader. The {term}`CLI`'s
`isec --in-place` is built on it — see the [CLI reference](../../cli.md#in-place-querying).

The snippets below continue from one another: each section reuses the `view` opened in
[Opening a view](#opening-a-view) and, later, the `hits` from [Querying](#querying).

## Opening a view

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

`genogrove::structure::grove_view` takes the same three {term}`template` parameters as `grove`;
they must match the grove that wrote the file. `open` takes a **file path** because partial reading
seeks to individual block offsets, which needs a {term}`seekable` source.

```cpp
#include <genogrove/structure/grove/grove_view.hpp>
#include <genogrove/data_type/interval.hpp>

namespace gdt = genogrove::data_type;
namespace gst = genogrove::structure;

// A plain file written by grove::serialize()
auto view = gst::grove_view<gdt::interval, std::string>::open("grove.gg");
```

The second argument, `data_offset`, is the byte offset at which the grove stream starts. It defaults
to `0`, which is right for a file written by `grove::serialize`. A `.gg` written by the
{doc}`CLI </cli>` starts with a 12-byte {doc}`file header <format>`, so pass `gio::gg_header::SIZE`
to skip it:

```cpp
#include <genogrove/io/gg_format.hpp>
#include <genogrove/io/bed_reader.hpp>

namespace gio = genogrove::io;

// A BED index written by `genogrove idx`: interval keys, bed_entry payloads, string edge labels
auto cli_view = gst::grove_view<gdt::interval, gio::bed_entry, std::string>::open(
    "index.gg", gio::gg_header::SIZE);
```

`open` throws `std::runtime_error` (an {term}`exception`) on a missing file, a bad {term}`magic`
value, a non-seekable or truncated {term}`stream`, or a malformed directory. Hold the view by value
as returned from `open()` — that is, write `auto view = ...::open(...)` as above and keep using
that variable.

::::

::::{tab-item} {{ py_tab }}
:sync: py

There is one view class per grove class: `GroveView`, `NumericGroveView`, `KmerGroveView`,
`BedGroveView` and `GffGroveView`. Each returns the {term}`Key <key>` / {term}`QueryResult` types
of its grove. Open a file with the view class that matches the grove class that wrote it (see
{doc}`/guide/grove/index` for the grove classes). `open` takes a **file path** because partial
reading seeks to individual block offsets, which needs a {term}`seekable` source.

```python
import pygenogrove as pg

# A file written by Grove.serialize()
view = pg.GroveView.open("grove.gg")
```

```python
GroveView.open(path: str, data_offset: int = 0) -> GroveView
```

`data_offset` is the byte offset at which the grove stream starts; `0` is right for a file written
by `serialize()`. Pass a non-zero offset only for a `.gg` that has something in front of the grove
stream, such as the 12-byte {doc}`file header <format>` the {doc}`genogrove CLI </cli>` writes.
`open` raises `RuntimeError` (an {term}`exception`) on a missing file, a bad {term}`magic` value, a
non-seekable source or a malformed directory. It {term}`releases the GIL <GIL>`.

::::

:::::

## Querying

`intersect` ({term}`overlap` search) and {term}`flanking` have the same signatures and return the
same results as on the eager grove — they share the query engine. The difference is only in what
gets read: `intersect` pages in the descent path plus the overlapping leaves; `flanking` may page
in a few more blocks, because it can branch into both sides of the query.

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

Continuing with `view` from above:

```cpp
// Overlap query within one index, or across every index
auto hits = view.intersect(gdt::interval{100, 200}, "chr1");
auto all  = view.intersect(gdt::interval{100, 200});

// Nearest non-overlapping neighbours on either side
auto fl = view.flanking(gdt::interval{100, 200}, "chr1");
if (fl.get_predecessor()) { /* ... */ }   // nullptr if there is none

// Predicate-filtered flanking, applied at leaf candidates only
auto same_side = view.flanking(gdt::interval{100, 200}, "chr1",
    [](const gdt::interval& candidate, const gdt::interval& query) { return true; });
```

The optional third argument is a filter function (a {term}`predicate`, here a {term}`lambda`)
that decides which neighbour candidates count; it never changes how much of the tree is read.
Precisely: the `flanking` predicate {term}`overload` applies `is_compatible` at **leaf candidates
only** — the internal nodes above the leaves are skipped or descended purely on the position ranges
they summarise (aggregate ranges), without consulting the predicate — exactly as in
`grove::flanking`. Either result field may be null (a {term}`pointer` to nothing); both are null if
the index is absent. See {doc}`/guide/grove/querying` for the semantics.

::::

::::{tab-item} {{ py_tab }}
:sync: py

Continuing with `view` from above (`"*"` is the any-{term}`strand` wildcard):

```python
# Overlap query within one index, or across every index
hits = view.intersect(pg.GenomicCoordinate("*", 100, 200), "chr1")
all_hits = view.intersect(pg.GenomicCoordinate("*", 100, 200))

# Nearest non-overlapping neighbours on either side
fl = view.flanking(pg.GenomicCoordinate("*", 100, 200), "chr1")
fl.predecessor, fl.successor          # each a Key or None

# Same-strand neighbours only; the predicate sees key values, not Keys
fl = view.flanking(pg.GenomicCoordinate("+", 100, 200), "chr1",
                   lambda cand, q: cand.strand == q.strand)
```

The optional third argument is a filter function (a {term}`predicate`, here a {term}`lambda`) that
decides which neighbour candidates count. It is applied at leaf candidates only, exactly as in
`Grove.flanking`; exceptions it raises propagate out. Queries hold the GIL,
because a query pages blocks into the view's cache. See {doc}`/guide/grove/querying` for the
semantics.

::::

:::::

## Following graph edges

A view can follow the {doc}`graph overlay </guide/graph/index>` too, in both directions. Following
an {term}`edge` pages in only the block that holds the other endpoint, so hopping to a key on
another chromosome costs one block load. Edge counts and {term}`edge metadata` are stored next to
the key itself, so reading them loads nothing extra.

The snippets reuse `hits` from [Querying](#querying). They are shown for a file whose grove has
edges — `grove.gg` from the {doc}`saving example <index>` has none, so there they would find
nothing to follow.

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

`cli_view` is the header-skipping view from [Opening a view](#opening-a-view).

```cpp
for (auto* k : hits.get_keys()) {
    for (auto* nbr : view.get_neighbors(k))    { /* outgoing: k -> nbr */ }
    for (auto* src : view.get_in_neighbors(k)) { /* incoming: src -> k */ }
    auto n_out = view.out_degree(k);
    auto n_in  = view.in_degree(k);
}

// Edge-carrying views only (edge_data_type != void), e.g. cli_view from "Opening a view"
auto cli_hits = cli_view.intersect(gdt::interval{100, 200}, "chr1");
for (auto* k : cli_hits.get_keys()) {
    auto labels = cli_view.get_edges(k);                              // std::vector<std::string>
    auto pairs  = cli_view.get_edge_list(k);                          // {target key*, label}
    auto strong = cli_view.get_neighbors_if(k,
        [](const std::string& label) { return label == "activates"; });
}
```

Key pointers passed in must be ones this view produced. The key-resolving accessors (those that
return keys) throw `std::invalid_argument` on a null pointer; `get_edges` / `get_in_edges` return
an empty vector and `out_degree` / `in_degree` return `0` instead — the same split as
`graph_overlay`.

::::

::::{tab-item} {{ py_tab }}
:sync: py

The `m["weight"] > 5` filter assumes edges whose metadata is a dict with a `weight` entry, as built
in {doc}`/guide/graph/building`.

```python
for key in hits:
    for nbr in view.get_neighbors(key):      # outgoing: key -> nbr
        ...
    for src in view.get_in_neighbors(key):   # incoming: src -> key
        ...
    view.out_degree(key), view.in_degree(key)

    # Edge-carrying views only (GroveView, NumericGroveView, KmerGroveView)
    view.get_edges(key)                      # metadata, parallel to get_neighbors(key)
    view.get_edge_list(key)                  # [(target Key, metadata), ...]
    view.get_neighbors_if(key, lambda m: m is not None and m["weight"] > 5)
```

Keys passed in must be ones this view produced. Every accessor raises `TypeError` if the key is
`None`. Edge metadata is the **decoded** payload, which is `None` for an edge added without one, so
guard for it in a predicate when labelled and unlabelled edges are mixed.

`get_edges`, `get_edge_list`, `get_neighbors_if` and their `get_in_*` counterparts exist only on the
**universal `GroveView`** and its point-key siblings `NumericGroveView` / `KmerGroveView`, whose
edges carry a payload. The typed `BedGroveView` / `GffGroveView` keep unlabelled edges, mirroring
`BedGrove` / `GffGrove`, so on those use `get_neighbors` / `get_in_neighbors` to traverse.

::::

:::::

## Introspection

Before querying you may want to know what the file contains; after querying you may want proof that
the read really was partial.

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

```cpp
#include <cassert>

view.get_order();           // B+ tree order the file was built with
view.get_index_names();     // std::vector<std::string>, unspecified order
view.blocks_loaded();       // blocks paged in so far
view.block_count();         // total blocks in the file
assert(view.blocks_loaded() < view.block_count());   // the query was partial
```

`get_order()` is the tree {term}`order` the grove was built with (the `100` in `grove(100)`).
`get_index_names()` reads nothing beyond the directory already loaded at `open()`. Unlike
`grove::get_root_nodes()`, which hands back live {term}`node` pointers, the view returns a copied
name list — a lazy reader has no persistent root nodes.

::::

::::{tab-item} {{ py_tab }}
:sync: py

```python
view.get_order()            # B+ tree order the file was built with
view.get_index_names()      # list[str], unspecified order
view.blocks_loaded()        # blocks paged in so far
view.block_count()          # total blocks in the file (0 for an empty grove)
assert view.blocks_loaded() < view.block_count()     # the query was partial
```

`get_order()` is the tree {term}`order` the grove was built with (the `100` in `Grove(100)`).
`get_index_names()` reads nothing beyond the directory already loaded at `open()`. The eager `Grove`
has no equivalent — see {doc}`/guide/grove/index`.

::::

:::::

## Methods

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

`grove_view<key_type, data_type = void, edge_data_type = void>` in
`genogrove/structure/grove/grove_view.hpp`. Every method is `[[nodiscard]]` ({term}`nodiscard`).

Methods:

- `static grove_view open(const std::string& path, std::streamoff data_offset = 0)` — open a `.gg`;
  throws `std::runtime_error`
- `intersect(const key_type& query, std::string_view index)` /
  `intersect(const key_type& query)` → `query_result`
- `flanking(const key_type& query, std::string_view index)` /
  `flanking(query, index, Pred is_compatible)` → `flanking_query_result` (`get_predecessor()` /
  `get_successor()`, each a key pointer or `nullptr`)
- `get_neighbors(const key* source)` / `get_in_neighbors(const key* target)` →
  `std::vector<key*>`; throw `std::invalid_argument` on null
- `out_degree(const key* source)` / `in_degree(const key* target)` → `std::size_t`; `0` for null
- `get_order()` → `int`
- `get_index_names()` → `std::vector<std::string>`
- `blocks_loaded()` → `std::size_t`; `block_count()` → `uint32_t` block id

Edge-carrying views only (`edge_data_type != void`):

- `get_edges(const key* source)` / `get_in_edges(const key* target)` →
  `std::vector<edge_data_type>` in edge order; empty for null
- `get_neighbors_if(const key* source, Pred pred)` / `get_in_neighbors_if(const key* target, Pred pred)`
  → `std::vector<key*>` whose edge metadata satisfies `pred(const edge_data_type&)`; throw on null
- `get_edge_list(const key* source)` / `get_in_edge_list(const key* target)` →
  `std::vector<std::pair<key*, edge_data_type>>` in edge order; throw on null

::::

::::{tab-item} {{ py_tab }}
:sync: py

`GroveView`, `NumericGroveView`, `KmerGroveView`, `BedGroveView`, `GffGroveView`. Full signatures in
the {doc}`Python API reference </reference/python/grove>`.

Methods:

- `GroveView.open(path, data_offset=0)` *(static)* → view; raises `RuntimeError`; releases the GIL
- `intersect(query)` / `intersect(query, index)` → `QueryResult`
- `flanking(query, index)` / `flanking(query, index, is_compatible)` → `FlankingResult`
- `get_neighbors(source)` / `get_in_neighbors(target)` → `list[Key]`; `TypeError` on `None`
- `out_degree(source)` / `in_degree(target)` → `int`; `TypeError` on `None`
- `get_order()` → `int`
- `get_index_names()` → `list[str]`
- `blocks_loaded()` / `block_count()` → `int`

`GroveView` / `NumericGroveView` / `KmerGroveView` only:

- `get_edges(source)` / `get_in_edges(target)` → `list` of metadata (or `None`) in edge order
- `get_neighbors_if(source, predicate)` / `get_in_neighbors_if(target, predicate)` → `list[Key]`
- `get_edge_list(source)` / `get_in_edge_list(target)` → `list[tuple[Key, metadata]]`

All raise `TypeError` on `None`.

::::

:::::

## Semantics

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

- **Non-copyable and non-movable** — keep the view in the variable `open()` returned; it cannot be
  copied or moved afterwards. It owns the file and a {term}`zlib` decompression state. Hold it by
  value from `open()`; the return is guaranteed copy elision, so no move is needed.
- **The block cache never evicts** — every block a query reads stays in memory until the view is
  destroyed, so memory grows with the set of blocks touched, bounded by the query footprint (the
  distinct blocks your queries reach), and never shrinks.
- **Not {term}`thread-safe`** — a query pages in blocks on demand, so use one view per thread.
- **Key pointers** a view returns point into its block cache and are valid only while the view is
  alive.
- Requires a **{term}`format <format version>` 0.3** `.gg` (genogrove v0.26.1+; see
  {doc}`format`). Match the template arguments to the grove that wrote the file; the stream does
  not record them.

::::

::::{tab-item} {{ py_tab }}
:sync: py

- **The block cache never evicts** — every block a query reads stays in memory for as long as the
  view (and any `Key` it returned) is alive, so memory grows with the set of blocks touched,
  bounded by the query footprint (the distinct blocks your queries reach), and never shrinks.
- **Not {term}`thread-safe`** — a query mutates the block cache and holds the GIL, so concurrent
  Python threads take turns on view I/O; use **one view per thread**.
- **Keys** a view returns point into its own storage and are valid only while the view is alive.
  A `Key` keeps its view alive for as long as you hold it.
- Requires a **{term}`format <format version>` 0.3** `.gg` (genogrove v0.26.1+, pygenogrove 0.8.0+;
  see {doc}`format`).
  Match the view class to the grove class that wrote the file; the file does not record it.

::::

:::::