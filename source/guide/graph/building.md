# Building a Graph

{term}`Edges <edge>` are created between **{term}`key handles <key>`**, so building a graph is a
matter of getting hold of the right handles — from inserts, {term}`bulk inserts <bulk insert>`,
queries or previous navigation — and calling `add_edge` for each pair, or `link_if` for a whole chain
at once. The C++ snippets use the `gdt::` / `gst::` shorthands and the Python snippets the `pg`
import from the first example in {doc}`index`.

## Adding an edge

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

```cpp
void add_edge(key* source, key* target);                  // plain edge
void add_edge(key* source, key* target, M&& metadata);    // when edge_data_type != void
```

`M` stands for the grove's {term}`edge metadata` type, its third {term}`template` argument.

```cpp
gst::grove<gdt::interval, std::string, double> g(100);

auto* exon1 = g.insert_data("chr1", gdt::interval{100, 200}, "exon1");
auto* exon2 = g.insert_data("chr1", gdt::interval{300, 400}, "exon2");

g.add_edge(exon1, exon2, 0.95);     // exon1 -> exon2, weight 0.95
```

Both handles must belong to this grove. A {term}`null pointer <pointer>` throws
`std::invalid_argument`. Keys from different {term}`indices <index>` (chromosomes) can be linked.

::::

::::{tab-item} {{ py_tab }}
:sync: py

```python
add_edge(source: Key, target: Key)            # payload None
add_edge(source: Key, target: Key, data)      # JSON payload (labelled groves only)
```

`data` is the {term}`edge metadata`, any JSON value.

```python
g = pg.Grove(100)

exon1 = g.insert("chr1", pg.GenomicCoordinate("+", 100, 200), "exon1")
exon2 = g.insert("chr1", pg.GenomicCoordinate("+", 300, 400), "exon2")

g.add_edge(exon1, exon2, {"weight": 0.95})    # exon1 -> exon2
```

Both keys must belong to this grove. `None` raises `TypeError`. Keys from different
{term}`indices <index>` (chromosomes) can be linked.

::::

:::::

## Where key handles come from

Any handle the grove has given you can be an edge endpoint:

- **inserts** return one handle; **bulk inserts** return a list of them in input order
- **queries** (`intersect`, `flanking`) return handles — link features by spatial relationship
- **navigation** (`get_neighbors`, …) returns handles — extend a graph from where you are

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

```cpp
gst::grove<gdt::interval, std::string> g(100);
g.insert_data("chr1", gdt::interval{1000, 2000}, "GeneA");
g.insert_data("chr1", gdt::interval{1500, 2500}, "GeneB");
g.insert_data("chr1", gdt::interval{2200, 3000}, "GeneC");
g.insert_data("chr1", gdt::interval{5000, 6000}, "GeneD");

// Link every pair of features that overlap a region
auto results = g.intersect(gdt::interval{1000, 3000}, "chr1");
const auto& hits = results.get_keys();              // GeneA, GeneB, GeneC
for (size_t i = 0; i < hits.size(); ++i) {
    for (size_t j = i + 1; j < hits.size(); ++j) {
        g.add_edge(hits[i], hits[j]);
    }
}
```

`get_keys()` returns the matching handles (the C++ counterpart of Python's {term}`QueryResult`);
`const auto&` names that list without copying it (see {term}`const`).

::::

::::{tab-item} {{ py_tab }}
:sync: py

```python
g = pg.Grove(100)
for name, s, e in [("GeneA", 1000, 2000), ("GeneB", 1500, 2500),
                   ("GeneC", 2200, 3000), ("GeneD", 5000, 6000)]:
    g.insert("chr1", pg.GenomicCoordinate("+", s, e), name)

# Link every pair of features that overlap a region
hits = list(g.intersect(pg.GenomicCoordinate("*", 1000, 3000), "chr1"))   # GeneA, GeneB, GeneC
for i, a in enumerate(hits):
    for b in hits[i + 1:]:
        g.add_edge(a, b)
```

`intersect` returns a {term}`QueryResult`, which can be looped over but not sliced; `list(...)`
turns it into a plain list so `hits[i + 1:]` works.

::::

:::::

## Linking consecutive keys

Given keys in order — typically the list a bulk insert returned — `link_if` adds an edge between
each adjacent pair `(keys[i], keys[i+1])` for which a {term}`predicate` (a function that answers
yes or no for a pair) says yes. This is the idiom for chaining exons into transcripts.

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

One function, two predicate shapes. Returning `bool` adds a plain edge; returning
`std::optional<edge_data_type>` (a value that may be empty) adds an edge **with** that metadata when
the optional holds a value and skips the pair when it is empty. The predicates below are
{term}`lambdas <lambda>` — unnamed functions written inline — that receive the two key handles:

```cpp
// Plain edges: link exons that belong to the same transcript
// ExonInfo: your own struct with a transcript_id field;
// exon_data: a std::vector<std::pair<gdt::interval, ExonInfo>> sorted by start
gst::grove<gdt::interval, ExonInfo> g(100);
auto exons = g.insert_data("chr1", exon_data, gst::sorted, gst::bulk);

g.link_if(exons, [](auto* k1, auto* k2) {
    return k1->get_data().transcript_id == k2->get_data().transcript_id;
});

// Labelled edges: store the intron length, skip implausibly long gaps
// data: a std::vector<std::pair<gdt::interval, std::string>> sorted by start
gst::grove<gdt::interval, std::string, double> w(100);
auto keys = w.insert_data("chr1", data, gst::sorted, gst::bulk);

w.link_if(keys, [](auto* k1, auto* k2) -> std::optional<double> {
    auto start = k2->get_value().get_start();
    auto end   = k1->get_value().get_end();
    if (start <= end) return std::nullopt;            // overlapping or touching: no intron
    size_t intron = start - end - 1;                  // bases strictly between the closed intervals
    if (intron < 100000) return static_cast<double>(intron);
    return std::nullopt;
});
```

`link_if` works on any `std::vector<key*>`, including one you assembled by hand or took from a
query result. The predicate must satisfy `std::invocable<Predicate, key*, key*>`, i.e. it must be
callable with two `key*` arguments. See {doc}`editing` for the rules that apply to all predicate
callbacks.

::::

::::{tab-item} {{ py_tab }}
:sync: py

Two methods: `link_if` for plain edges, `link_with` for labelled ones (universal `Grove` and the
point groves `NumericGrove` / `KmerGrove` only). The predicate can be a {term}`lambda` (an unnamed
one-line function) or an ordinary `def` function:

```python
g = pg.Grove(100)

# Plain edges: link exons that belong to the same transcript
# items: list of (GenomicCoordinate, data) tuples, data being a dict with a "tx" entry
exons = g.insert_bulk("chr1", items)      # list[Key], in input order
g.link_if(exons, lambda k1, k2: k1.data["tx"] == k2.data["tx"])

# Labelled edges: store the intron length, skip implausibly long gaps
def intron(k1, k2):
    gap = k2.value.start - k1.value.end - 1               # bases strictly between the closed intervals
    return {"intron": gap} if 0 <= gap < 100_000 else None   # None = no edge (also for overlaps)

g.link_with(exons, intron)
```

```python
link_if(keys: list[Key], predicate: (Key, Key) -> bool)
link_with(keys: list[Key], predicate: (Key, Key) -> object | None)
```

Both work on any list of keys, including one you assembled by hand or took from a query result. A
`None` element in `keys` raises `TypeError`. Both methods call back into Python for every pair and
{term}`hold the GIL <GIL>`; see {doc}`editing` for the rules that apply to all predicate callbacks.

::::

:::::

## External (graph-only) keys

Some nodes belong in the graph but not in the tree: a transcription factor that regulates genes, a
transcript that groups exons, a sample identifier. An **{term}`external key`** participates in edges
exactly like an indexed key but is never returned by `intersect` or `flanking`, and it is owned,
serialized and restored with the grove.

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

```cpp
key* add_external_key(key_type value, data_type data);   // data-carrying groves
key* add_external_key(key_type value);                   // dataless groves (data_type = void)
```

The key value is required by the type but unused for queries; any placeholder works.

```cpp
gst::grove<gdt::interval, std::string, double> g(100);

auto* brca1 = g.insert_data("chr1", gdt::interval{10000, 15000}, "BRCA1");
auto* tp53  = g.insert_data("chr1", gdt::interval{20000, 25000}, "TP53");

auto* tf = g.add_external_key(gdt::interval{0, 0}, "E2F1");   // graph-only node

g.add_edge(tf, brca1, 0.95);
g.add_edge(tf, tp53, 0.87);

g.get_neighbors(tf).size();                                   // 2
g.intersect(gdt::interval{0, 40000}, "chr1").get_keys().size(); // 2 — tf is not indexed

g.indexed_vertex_count();    // 2
g.external_vertex_count();   // 1
g.vertex_count();            // 3
```

External keys mix freely with indexed keys in `link_if` vectors and in every graph accessor. Unlike
indexed keys, their handles survive {term}`compact() <compact>` (see {doc}`/guide/grove/removing`).

::::

::::{tab-item} {{ py_tab }}
:sync: py

```python
add_external_key(key: GenomicCoordinate, data=None) -> Key
```

The coordinate is required by the type but unused for queries; any placeholder works.

```python
g = pg.Grove(100)

brca1 = g.insert("chr1", pg.GenomicCoordinate("+", 10000, 15000), "BRCA1")
tp53  = g.insert("chr1", pg.GenomicCoordinate("+", 20000, 25000), "TP53")

tf = g.add_external_key(pg.GenomicCoordinate(".", 0, 0), {"name": "E2F1"})   # graph-only

g.add_edge(tf, brca1, {"weight": 0.95})
g.add_edge(tf, tp53, {"weight": 0.87})

len(g.get_neighbors(tf))                                            # 2
len(g.intersect(pg.GenomicCoordinate("*", 0, 40000), "chr1"))       # 2 — tf is not indexed

g.indexed_vertex_count(), g.external_vertex_count(), g.vertex_count()   # 2, 1, 3
```

External keys mix freely with indexed keys in `link_if` / `link_with` lists and in every graph
accessor. Unlike indexed keys, they are **not** invalidated by {term}`compact() <compact>` (see
{doc}`/guide/grove/removing`).

::::

:::::
