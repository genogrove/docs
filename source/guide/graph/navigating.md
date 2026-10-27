# Navigating a Graph

Every edge is stored once and indexed under **both** of its endpoints, so each read has a forward
form (from the source: *what does this key point to?*) and a reverse form (from the target: *what
points at this key?*) at the same cost. The reverse accessors share the forward name with an `in_`
prefix: `get_neighbors` / `get_in_neighbors`, `out_degree` / `in_degree`, and so on.

## Neighbours in both directions

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

```cpp
std::vector<key*> get_neighbors(const key* source) const;      // targets of source's outgoing edges
std::vector<key*> get_in_neighbors(const key* target) const;   // sources of target's incoming edges
bool has_edge(const key* source, const key* target) const;
```

```cpp
gst::grove<gdt::interval, std::string, double> g(100);
auto* enh1 = g.insert_data("chr1", gdt::interval{1000, 1500}, "Enh1");
auto* enh2 = g.insert_data("chr1", gdt::interval{2000, 2500}, "Enh2");
auto* gene = g.insert_data("chr1", gdt::interval{5000, 10000}, "Gene1");

g.add_edge(enh1, gene, 0.9);
g.add_edge(enh2, gene, 0.6);

g.get_neighbors(enh1);          // {gene}        — what Enh1 regulates
g.get_in_neighbors(gene);       // {enh1, enh2}  — what regulates Gene1, no mirrored edges needed
g.has_edge(enh1, gene);         // true
```

Results are in edge-insertion order; a parallel edge yields a repeated entry. Pointers are ordinary
key handles.

::::

::::{tab-item} {{ py_tab }}
:sync: py

```python
get_neighbors(source: Key) -> list[Key]      # targets of source's outgoing edges
get_in_neighbors(target: Key) -> list[Key]   # sources of target's incoming edges
has_edge(source: Key, target: Key) -> bool
```

```python
g = pg.Grove(100)
enh1 = g.insert("chr1", pg.GenomicCoordinate("+", 1000, 1500), "Enh1")
enh2 = g.insert("chr1", pg.GenomicCoordinate("+", 2000, 2500), "Enh2")
gene = g.insert("chr1", pg.GenomicCoordinate("+", 5000, 10000), "Gene1")

g.add_edge(enh1, gene, {"weight": 0.9})
g.add_edge(enh2, gene, {"weight": 0.6})

g.get_neighbors(enh1)           # [gene]        — what Enh1 regulates
g.get_in_neighbors(gene)        # [enh1, enh2]  — what regulates Gene1, no mirrored edges needed
g.has_edge(enh1, gene)          # True
```

Results are in edge-insertion order; a parallel edge yields a repeated entry. Available on every
grove, including `BedGrove` / `GffGrove`.

::::

:::::

## Edge metadata and edge lists

Three views of the same edges: the metadata alone, the metadata paired with the other endpoint, or
(C++) the full edge record.

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

```cpp
std::vector<M>    get_edges(const key* source) const;         // metadata of outgoing edges   (edge_data_type != void)
std::vector<M>    get_in_edges(const key* target) const;      // metadata of incoming edges   (edge_data_type != void)
std::vector<edge> get_edge_list(const key* source) const;     // full outgoing edges          (always)
std::vector<edge> get_in_edge_list(const key* target) const;  // full incoming edges          (always)
```

`edge` has three fields: `source`, `target` and `metadata`; on a plain-edge grove (`void` edge type)
`metadata` is `std::monostate`. The lists are returned **by value**.

```cpp
g.get_edges(enh1);                 // {0.9}
g.get_in_edges(gene);              // {0.9, 0.6}

for (const auto& e : g.get_edge_list(enh1)) {
    std::cout << e.target->get_data() << " weight " << e.metadata << "\n";
}
for (const auto& e : g.get_in_edge_list(gene)) {
    std::cout << e.source->get_data() << " -> Gene1 weight " << e.metadata << "\n";
}
```

::::

::::{tab-item} {{ py_tab }}
:sync: py

Available on the labelled groves (`Grove`, `NumericGrove`, `KmerGrove`):

```python
get_edges(source: Key) -> list                              # payloads of outgoing edges
get_in_edges(target: Key) -> list                           # payloads of incoming edges
get_edge_list(source: Key) -> list[tuple[Key, object]]      # (target, payload) pairs
get_in_edge_list(target: Key) -> list[tuple[Key, object]]   # (source, payload) pairs
```

Payloads are returned as decoded copies; an edge added without a payload yields `None`.

```python
g.get_edges(enh1)                  # [{'weight': 0.9}]
g.get_in_edges(gene)               # [{'weight': 0.9}, {'weight': 0.6}]

for target, meta in g.get_edge_list(enh1):
    print(target.data, meta["weight"])
for source, meta in g.get_in_edge_list(gene):
    print(source.data, "-> Gene1", meta["weight"])
```

::::

:::::

## Filtering by metadata

`get_neighbors_if` / `get_in_neighbors_if` return only the neighbours whose edge metadata satisfies
a predicate. The predicate sees the **metadata stored on the edge** and nothing else; the grove
derives nothing from the coordinates. To filter on distance, compute it when you add the edge and
store it as the metadata.

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

```cpp
// edge_data_type = size_t: each edge carries a caller-supplied distance in bp
gst::grove<gdt::interval, std::string, size_t> g(100);

auto* gene1 = g.insert_data("chr1", gdt::interval{1000, 2000}, "GeneA");
auto* gene2 = g.insert_data("chr1", gdt::interval{10000, 11000}, "GeneB");
auto* gene3 = g.insert_data("chr1", gdt::interval{50000, 51000}, "GeneC");

// Caller computes the gap (bases strictly between two closed intervals)
// and stores it as the edge's metadata
auto gap = [](const auto* a, const auto* b) {
    return b->get_value().get_start() - a->get_value().get_end() - 1;
};
g.add_edge(gene1, gene2, gap(gene1, gene2));   // edge gene1 -> gene2 stores 7999
g.add_edge(gene1, gene3, gap(gene1, gene3));   // edge gene1 -> gene3 stores 47999

// The predicate is called once per outgoing edge of gene1 with that edge's
// metadata (7999, then 47999); targets of accepted edges are returned.
auto nearby = g.get_neighbors_if(gene1,
    [](size_t distance) { return distance <= 10000; });          // {gene2}

// Reverse: the same predicate over the edges pointing AT gene2
auto nearby_sources = g.get_in_neighbors_if(gene2,
    [](size_t distance) { return distance <= 10000; });          // {gene1}
```

Both require `std::predicate<Predicate, const edge_data_type&>` and exist only when
`edge_data_type` is not `void`.

::::

::::{tab-item} {{ py_tab }}
:sync: py

```python
g = pg.Grove(100)
gene1 = g.insert("chr1", pg.GenomicCoordinate("+", 1000, 2000), "GeneA")
gene2 = g.insert("chr1", pg.GenomicCoordinate("+", 10000, 11000), "GeneB")
gene3 = g.insert("chr1", pg.GenomicCoordinate("+", 50000, 51000), "GeneC")

# Caller computes the gap (bases strictly between two closed intervals)
# and stores it as the edge's payload
def gap(a, b):
    return b.value.start - a.value.end - 1

g.add_edge(gene1, gene2, {"distance": gap(gene1, gene2)})   # stores 7999
g.add_edge(gene1, gene3, {"distance": gap(gene1, gene3)})   # stores 47999

# The predicate is called once per outgoing edge of gene1 with that edge's
# payload; targets of accepted edges are returned.
g.get_neighbors_if(gene1, lambda m: m["distance"] <= 10000)        # [gene2]

# Reverse: the same predicate over the edges pointing AT gene2
g.get_in_neighbors_if(gene2, lambda m: m["distance"] <= 10000)     # [gene1]
```

Guard for `None` when a grove mixes labelled and unlabelled edges
(`lambda m: m is not None and ...`). Labelled groves only; the predicate holds the GIL (see
{doc}`editing` for the callback rules).

::::

:::::

## Degrees and counts

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

```cpp
std::size_t out_degree(const key* source) const;   // outgoing edges of one key
std::size_t in_degree(const key* target) const;    // incoming edges of one key
size_t edge_count() const;                          // all edges in the grove
size_t vertex_count_with_edges() const;             // keys with at least one outgoing edge
bool   graph_empty() const;                         // edge_count() == 0
```

```cpp
g.out_degree(enh1);              // 1
g.in_degree(gene);               // 2
g.edge_count();                  // 2
g.vertex_count_with_edges();     // 2 (enh1, enh2) — gene only receives
```

Key totals (`vertex_count`, `indexed_vertex_count`, `external_vertex_count`) are described in
{doc}`/guide/grove/removing`.

::::

::::{tab-item} {{ py_tab }}
:sync: py

```python
out_degree(source: Key) -> int          # outgoing edges of one key
in_degree(target: Key) -> int           # incoming edges of one key
edge_count() -> int                     # all edges in the grove
vertex_count_with_edges() -> int        # keys with at least one outgoing edge
graph_empty() -> bool                   # edge_count() == 0
```

```python
g.out_degree(enh1)               # 1
g.in_degree(gene)                # 2
g.edge_count()                   # 2
g.vertex_count_with_edges()      # 2 (enh1, enh2) — gene only receives
```

Key totals (`vertex_count`, `indexed_vertex_count`, `external_vertex_count`) are described in
{doc}`/guide/grove/removing`.

::::

:::::

## Null arguments

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

The read accessors take `const key*`; passing a non-const handle converts implicitly. The accessors
that must dereference a key to follow an edge — `get_neighbors`, `get_in_neighbors`,
`get_neighbors_if`, `get_in_neighbors_if`, `get_edge_list`, `get_in_edge_list`, and `add_edge` —
throw `std::invalid_argument` on a null pointer. The metadata-only accessors `get_edges` /
`get_in_edges` have nothing to dereference and return an empty vector; `has_edge`, `out_degree` and
`in_degree` return `false` / `0`. The partial reader `grove_view` follows the same split.

::::

::::{tab-item} {{ py_tab }}
:sync: py

Every graph method that takes a `Key` raises `TypeError` when given `None`, and `link_if` /
`link_with` raise `TypeError` for a `None` element in `keys`. The only method that accepts `None` is
`remove_key`, which returns `False` for it.

::::

:::::