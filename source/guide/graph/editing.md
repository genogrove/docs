# Editing a Graph

{term}`Edges <edge>` can be removed one at a time, in bulk by endpoint, by {term}`predicate` (a
function you supply that says yes or no for each edge), or all at once. Removing edges never removes
{term}`keys <key>`. Conversely, removing a key (see {doc}`/guide/grove/removing`) drops all of its
edges automatically. The C++ snippets use the `gdt::` / `gst::` shorthands and the Python snippets
the `pg` import from the first example in {doc}`index`.

## Removing one edge

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

```cpp
bool remove_edge(key* source, key* target);   // true if an edge was found and removed
```

```cpp
gst::grove<gdt::interval, std::string, double> g(100);
auto* gene1 = g.insert_data("chr1", gdt::interval{1000, 2000}, "GeneA");
auto* gene2 = g.insert_data("chr1", gdt::interval{3000, 4000}, "GeneB");
auto* gene3 = g.insert_data("chr1", gdt::interval{5000, 6000}, "GeneC");

g.add_edge(gene1, gene2, 0.95);
g.add_edge(gene1, gene3, 0.45);

if (g.remove_edge(gene1, gene3)) {        // drop the low-confidence edge
    std::cout << "removed\n";
}
```

With parallel edges, `remove_edge` removes the first matching `source → target` edge only.

::::

::::{tab-item} {{ py_tab }}
:sync: py

```python
remove_edge(source: Key, target: Key) -> bool   # True if an edge was found and removed
```

```python
g = pg.Grove(100)
gene1 = g.insert("chr1", pg.GenomicCoordinate("+", 1000, 2000), "GeneA")
gene2 = g.insert("chr1", pg.GenomicCoordinate("+", 3000, 4000), "GeneB")
gene3 = g.insert("chr1", pg.GenomicCoordinate("+", 5000, 6000), "GeneC")

g.add_edge(gene1, gene2, {"weight": 0.95})
g.add_edge(gene1, gene3, {"weight": 0.45})

g.remove_edge(gene1, gene3)        # True — the low-confidence edge is gone
```

With parallel edges, `remove_edge` removes the first matching `source → target` edge only.

::::

:::::

## Removing many edges

Each of these returns the number of edges removed. Removing by endpoint only has to look at the
edges touching that key, not at the whole graph; `remove_edges_if` has to look at every edge.
Deleting an edge then also updates the list kept for its *other* endpoint, so each deletion costs
extra in proportion to how many edges that other key has. Clearing a hub connected to many
high-degree keys, or removing most edges of a large graph with `remove_edges_if`, therefore takes
noticeably longer than the candidate scan alone.

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

```cpp
size_t remove_edges_from(key* source);   // all outgoing edges of source
size_t remove_edges_to(key* target);     // all incoming edges of target
size_t remove_all_edges(key* key);       // both directions
size_t remove_edges_if(Predicate p);     // every edge e with p(const edge& e) == true
```

Continuing from the grove above, after putting the removed edge back and adding one more:

```cpp
g.add_edge(gene1, gene3, 0.45);
g.add_edge(gene2, gene3, 0.80);

auto dropped = g.remove_edges_if(                  // threshold on metadata: drops gene1 -> gene3
    [](const auto& e) { return e.metadata < 0.5; });   // 1

size_t pruned = g.remove_all_edges(gene2);         // gene1 -> gene2 and gene2 -> gene3: 2
```

The `remove_edges_if` predicate (here a {term}`lambda`, an unnamed function written inline)
receives the full `edge` struct (`source`, `target`, `metadata`) and must satisfy
`std::predicate<Predicate, const edge&>`, i.e. be callable with one `const edge&` and return `bool`.

::::

::::{tab-item} {{ py_tab }}
:sync: py

```python
remove_edges_from(source: Key) -> int    # all outgoing edges of source
remove_edges_to(target: Key) -> int      # all incoming edges of target
remove_all_edges(key: Key) -> int        # both directions
remove_edges_if(predicate) -> int        # every edge the predicate accepts
```

Continuing from the grove above, after putting the removed edge back and adding one more:

```python
g.add_edge(gene1, gene3, {"weight": 0.45})
g.add_edge(gene2, gene3, {"weight": 0.80})

# Universal / Numeric / Kmer grove: predicate(target, metadata) -> bool
dropped = g.remove_edges_if(lambda target, meta: meta is not None and meta["weight"] < 0.5)   # 1

pruned = g.remove_all_edges(gene2)                 # gene1 -> gene2 and gene2 -> gene3: 2

# BedGrove / GffGrove (unlabelled edges): predicate(target) -> bool
pg.BedGrove(100).remove_edges_if(lambda target: target.value.start > 1_000_000)   # 0 on an empty grove
```

The predicates above are {term}`lambdas <lambda>`, unnamed one-line functions. The predicate
signature depends on the grove: labelled groves pass `(target, metadata)`, the typed `BedGrove` /
`GffGrove` pass `(target)` only.

::::

:::::

## Finding one specific edge

Because `add_edge` does not deduplicate, a `source → target` pair can hold several parallel edges
with different metadata. When you need a particular one rather than the whole list, locate it by
its occurrence index.

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

`find_edge` and `edge_end` live on `graph_overlay` (the class that implements the
{term}`graph overlay`), not on `grove`; reach them through `grove::graph()`:

```cpp
using edge_iterator = std::list<edge>::iterator;        // graph_overlay::edge_iterator

edge_iterator find_edge(const key* source, const key* target, std::size_t occurrence = 0);
edge_iterator edge_end();                                // returned when no match exists
```

`find_edge` returns an {term}`iterator <iterator / iterable>` — a position inside the edge list,
read through with `->` — and `edge_end()` is the "not found" position to compare against:

```cpp
gst::grove<gdt::interval, std::string, std::string> g(100);
auto* exon1 = g.insert_data("chr1", gdt::interval{100, 200}, "exon1");
auto* exon2 = g.insert_data("chr1", gdt::interval{300, 400}, "exon2");
g.add_edge(exon1, exon2, "tx1");
g.add_edge(exon1, exon2, "tx2");                        // parallel edge

auto& ov = g.graph();
auto second = ov.find_edge(exon1, exon2, 1);             // the "tx2" edge (0-indexed)
if (second != ov.edge_end()) {
    std::cout << second->metadata << "\n";               // tx2
}
```

The iterator stays valid until that specific edge is erased; removing other edges does not
invalidate it.

::::

::::{tab-item} {{ py_tab }}
:sync: py

Not exposed. To pick one of several parallel edges, read them all with
`get_edge_list(source)` and select by position or payload:

```python
g = pg.Grove(100)
exon1 = g.insert("chr1", pg.GenomicCoordinate("+", 100, 200), "exon1")
exon2 = g.insert("chr1", pg.GenomicCoordinate("+", 300, 400), "exon2")
g.add_edge(exon1, exon2, {"tx": "tx1"})
g.add_edge(exon1, exon2, {"tx": "tx2"})                 # parallel edge

edges = g.get_edge_list(exon1)                    # [(exon2, {'tx': 'tx1'}), (exon2, {'tx': 'tx2'})]
second = edges[1]
```

::::

:::::

## Clearing the graph

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

```cpp
void clear_graph();          // remove every edge; keys and their tree positions are untouched
bool graph_empty() const;    // true when there are no edges
```

Continuing from the exon grove above:

```cpp
g.clear_graph();
g.graph_empty();                                       // true
g.intersect(gdt::interval{50, 150}, "chr1");           // keys are still there
```

A common pattern is to clear and rebuild with a different linking rule (e.g. a stricter
threshold in `link_if`, see {doc}`building`).

::::

::::{tab-item} {{ py_tab }}
:sync: py

```python
clear_graph() -> None        # remove every edge; keys and their tree positions are untouched
graph_empty() -> bool        # True when there are no edges
```

Continuing from the exon grove above:

```python
g.clear_graph()
g.graph_empty()                                              # True
len(g.intersect(pg.GenomicCoordinate("*", 50, 150), "chr1"))  # keys are still there
```

A common pattern is to clear and rebuild with a different linking rule (e.g. a stricter
threshold in `link_with`, see {doc}`building`).

::::

:::::

## Rules for predicate callbacks

`link_if` / `link_with`, `get_neighbors_if` / `get_in_neighbors_if` and `remove_edges_if` call your
predicate **while iterating the graph**. Two rules follow:

- **Do not mutate the graph from inside the predicate.** Calling `add_edge`, any `remove_edges_*`,
  `clear_graph` or `link_*` on the same grove while a predicate runs is undefined behaviour — anything
  may happen, including a crash or silently wrong results. Keep the predicate a pure inspector and
  mutate after the call returns.
- **Effects are applied as the iteration proceeds.** If the predicate throws an {term}`exception`
  part-way, the edges already added or removed stay added or removed; there is no rollback.

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

Predicates receive `key*` pairs (`link_if`), `const edge_data_type&` (`get_neighbors_if`), or
`const edge&` (`remove_edges_if`). Exceptions propagate to the caller.

::::

::::{tab-item} {{ py_tab }}
:sync: py

Predicates receive `Key` pairs (`link_if` / `link_with`), the decoded payload
(`get_neighbors_if`; `None` for an edge added without one), or `(target, metadata)` /
`(target)` (`remove_edges_if`). Exceptions propagate to the caller. All of these
{term}`hold the GIL <GIL>` for the duration of the call.

::::

:::::
