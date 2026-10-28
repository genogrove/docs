# Graph Overlay

Every {term}`grove` carries an optional **{term}`graph overlay`**: directed {term}`edges <edge>`
between the {term}`keys <key>` it stores. The tree answers *what is here?*; the graph answers *what
is this connected to?* — exon → next exon, enhancer → regulated gene, transcript → its exons. Edges
live inside the grove, can cross chromosomes, may carry their own {term}`metadata <edge metadata>`,
and are saved and restored with the grove.

The subpages cover each part:

- {doc}`building` — adding edges, linking consecutive keys, graph-only ({term}`external <external key>`) keys
- {doc}`navigating` — neighbours in both directions, edge metadata, filtering, degrees
- {doc}`editing` — removing edges, finding a specific edge, clearing the graph, {term}`predicate` rules

Edges are written to disk together with the grove; see the
{doc}`serialization guide </guide/serialization/index>` (including {term}`SIF` export for Cytoscape).

## A first graph

Three exons of one transcript, chained in transcription order, then walked forwards and backwards.
Edges are created between **{term}`key handles <key>`** — the values returned by inserts and queries.
The `100` passed when creating the grove is its {term}`order`; see {doc}`/guide/grove/index`.

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

```cpp
#include <genogrove/structure/grove/grove.hpp>
#include <genogrove/data_type/interval.hpp>
#include <iostream>

namespace gdt = genogrove::data_type;
namespace gst = genogrove::structure;

int main() {
    gst::grove<gdt::interval, std::string> transcript(100);   // plain edges (no metadata)

    auto* exon1 = transcript.insert_data("chr1", gdt::interval{1000, 1200}, "exon1");
    auto* exon2 = transcript.insert_data("chr1", gdt::interval{1500, 1700}, "exon2");
    auto* exon3 = transcript.insert_data("chr1", gdt::interval{2100, 2400}, "exon3");

    transcript.add_edge(exon1, exon2);   // exon1 -> exon2
    transcript.add_edge(exon2, exon3);   // exon2 -> exon3

    for (auto* next : transcript.get_neighbors(exon1)) {        // forwards: {exon2}
        std::cout << "after exon1: " << next->get_data() << "\n";
    }
    for (auto* prev : transcript.get_in_neighbors(exon3)) {     // backwards: {exon2}
        std::cout << "before exon3: " << prev->get_data() << "\n";
    }
    std::cout << transcript.edge_count() << " edges\n";          // 2
    return 0;
}
```

The `auto*` variables are {term}`pointers <pointer>` to the stored keys — the C++ form of a key
handle. The two `namespace` lines define the `gdt::` / `gst::` shorthands that every other C++
snippet on these pages uses.

::::

::::{tab-item} {{ py_tab }}
:sync: py

```python
import pygenogrove as pg

transcript = pg.Grove(100)

exon1 = transcript.insert("chr1", pg.GenomicCoordinate("+", 1000, 1200), "exon1")
exon2 = transcript.insert("chr1", pg.GenomicCoordinate("+", 1500, 1700), "exon2")
exon3 = transcript.insert("chr1", pg.GenomicCoordinate("+", 2100, 2400), "exon3")

transcript.add_edge(exon1, exon2)   # exon1 -> exon2
transcript.add_edge(exon2, exon3)   # exon2 -> exon3

[k.data for k in transcript.get_neighbors(exon1)]      # ['exon2']  forwards
[k.data for k in transcript.get_in_neighbors(exon3)]   # ['exon2']  backwards
transcript.edge_count()                                # 2
```

The `Key` objects returned by `insert` are the Python form of a key handle. Every other Python
snippet on these pages assumes the same `import pygenogrove as pg` line.

::::

:::::

## Edge metadata

An edge can carry a value of its own — a confidence score, a relationship type, an intron length.
Whether edges carry metadata, and of what type, is a property of the grove.

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

The grove's third {term}`template` parameter is the edge metadata type. Leave it out (or write
`void`) for plain edges; name a type to attach one value per edge:

```cpp
gst::grove<gdt::interval, std::string> plain(100);                  // edges carry nothing
gst::grove<gdt::interval, std::string, double> weighted(100);       // one double per edge

auto* a = weighted.insert_data("chr1", gdt::interval{100, 200}, "A");
auto* b = weighted.insert_data("chr1", gdt::interval{300, 400}, "B");
weighted.add_edge(a, b, 0.95);          // a -> b with weight 0.95
weighted.get_edges(a);                  // {0.95}
```

The metadata-dependent accessors (`get_edges`, `get_neighbors_if` and their `get_in_*` twins) exist
only when the edge type is not `void`; `get_edge_list` / `get_in_edge_list` always exist, with the
`metadata` field being `std::monostate` (an empty placeholder value) on plain-edge groves. For
several metadata shapes in one grove use a `std::variant` (a type that holds one of several
alternatives) as the edge type — but note that the default serializer handles only trivially
copyable types (plain values that can be copied byte for byte, such as numbers) and `std::string`,
so a grove with a `std::variant` edge type (or any other non-trivial metadata) needs a
`serialization_traits` specialization — a small piece of code telling the serializer how to write
and read that type — before it can be saved (see the
{doc}`serialization guide </guide/serialization/index>`).

::::

::::{tab-item} {{ py_tab }}
:sync: py

On the universal `Grove` (and `NumericGrove` / `KmerGrove`) every edge carries a JSON
{term}`payload`; the 2-argument `add_edge` attaches `None`:

```python
g = pg.Grove()
a = g.insert("chr1", pg.GenomicCoordinate("+", 100, 200), "A")
b = g.insert("chr1", pg.GenomicCoordinate("+", 300, 400), "B")
g.add_edge(a, b, {"type": "regulates", "weight": 0.95})
g.get_edges(a)                          # [{'type': 'regulates', 'weight': 0.95}]
```

Edge payloads must be finite JSON (`float('nan')` / `float('inf')` raise `ValueError`). The typed
`BedGrove` / `GffGrove` keep **unlabelled** edges so their {term}`.gg files <.gg file>` stay readable
by a plain C++ `grove<key_type, data_type>`; on them the labelled-edge methods (`add_edge` with a
payload, `get_edges`, `get_edge_list`, `get_neighbors_if`, `link_with` and the `get_in_*` variants)
are absent.

::::

:::::

## What an edge can connect

An edge joins any two key handles of the same grove: indexed keys from any chromosome, graph-only
**external keys** (see {doc}`building`), or a key with itself. Edges are **directed**: `a → b` does
not imply `b → a`, but every edge is readable from both ends (`get_neighbors(a)` and
`get_in_neighbors(b)`), so you never need to add the mirror image by hand.

`add_edge` **never deduplicates**: adding `a → b` twice stores two parallel edges, which is how two
transcripts can share an exon pair with different metadata. If you do not want duplicates, check
`has_edge` first or deduplicate your input.

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

```cpp
gst::grove<gdt::interval, std::string> g(100);
auto* a = g.insert_data("chr1", gdt::interval{100, 200}, "A");
auto* b = g.insert_data("chr1", gdt::interval{300, 400}, "B");

g.add_edge(a, b);
g.add_edge(a, b);            // second, parallel edge

g.out_degree(a);             // 2 — counts every edge
g.get_neighbors(a);          // {b, b}
g.has_edge(a, b);            // true — existence only
```

Both edges are serialized. A {term}`null pointer <pointer>` as `source` or `target` throws a
`std::invalid_argument` {term}`exception`.

::::

::::{tab-item} {{ py_tab }}
:sync: py

```python
g = pg.Grove(100)
a = g.insert("chr1", pg.GenomicCoordinate("+", 100, 200), "A")
b = g.insert("chr1", pg.GenomicCoordinate("+", 300, 400), "B")

g.add_edge(a, b)
g.add_edge(a, b)             # second, parallel edge

g.out_degree(a)              # 2 — counts every edge
g.get_neighbors(a)           # [b, b]
g.has_edge(a, b)             # True — existence only
```

Both edges are serialized. Passing `None` as either key raises a `TypeError` {term}`exception`.

::::

:::::

## Method overview

| Operation | C++ (`grove`) | Python (`Grove`) | Page |
|---|---|---|---|
| Add an edge | `add_edge(src, tgt[, meta])` | `add_edge(src, tgt[, data])` | {doc}`building` |
| Link consecutive keys | `link_if(keys, pred)` | `link_if` (plain) / `link_with` (labelled) | {doc}`building` |
| Graph-only key | `add_external_key(value[, data])` | `add_external_key(coord, data=None)` | {doc}`building` |
| Neighbours | `get_neighbors` / `get_in_neighbors` | same | {doc}`navigating` |
| Filtered neighbours | `get_neighbors_if` / `get_in_neighbors_if` | same (labelled groves) | {doc}`navigating` |
| Edge metadata | `get_edges` / `get_in_edges` | same (labelled groves) | {doc}`navigating` |
| Edges with endpoints | `get_edge_list` / `get_in_edge_list` | same, as `(key, data)` tuples | {doc}`navigating` |
| Existence and degree | `has_edge`, `out_degree`, `in_degree` | same | {doc}`navigating` |
| Counts | `edge_count`, `vertex_count_with_edges`, `graph_empty` | same | {doc}`navigating` |
| Remove edges | `remove_edge`, `remove_edges_from/to`, `remove_all_edges`, `remove_edges_if` | same | {doc}`editing` |
| Find one edge | `graph().find_edge` / `edge_end` | not exposed | {doc}`editing` |
| Clear | `clear_graph` | same | {doc}`editing` |

```{toctree}
:maxdepth: 1
:hidden:

building
navigating
editing
```
