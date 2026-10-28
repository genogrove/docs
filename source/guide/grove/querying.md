# Querying

A grove answers two questions: *which stored keys {term}`overlap` this region?* (`intersect`) and
*which stored keys are nearest on either side of this region without overlapping it?*
(`flanking`, see {term}`flanking`). Both take a query coordinate of the grove's {term}`key type`
and, optionally, an {term}`index` to restrict the search to one chromosome.

## Overlap queries

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
    gst::grove<gdt::interval, std::string> my_grove(100);
    my_grove.insert_data("chr1", gdt::interval{100, 200}, "gene1");
    my_grove.insert_data("chr1", gdt::interval{150, 250}, "gene2");
    my_grove.insert_data("chr1", gdt::interval{300, 400}, "gene3");
    my_grove.insert_data("chr2", gdt::interval{100, 200}, "gene4");

    // One index (chromosome) — the usual, faster form
    auto results = my_grove.intersect(gdt::interval{175, 225}, "chr1");
    for (auto* key : results.get_keys()) {
        std::cout << key->get_data() << " at " << key->get_value().to_string() << "\n";
    }
    // gene1, gene2 (gene3 does not overlap; gene4 is on chr2)

    // Every index
    auto all = my_grove.intersect(gdt::interval{175, 225});
    std::cout << all.get_keys().size() << " matches across all chromosomes\n";   // 3

    return 0;
}
```

The two {term}`overloads <overload>` `intersect(const key_type& query, std::string_view index)` and
`intersect(const key_type& query)` accept a value built on the spot (as above) and a named variable
alike; `const key_type&` means the query is only read and never changed. For
`genomic_coordinate` keys the overlap test is {term}`strand`-aware: two coordinates overlap when
their ranges share a base and their strands are equal **or either one is `'*'`**. A `'*'` query
matches any strand, a `'+'` query matches stored `'+'` and `'*'` keys, and a `'.'` query matches
stored `'.'` and `'*'` keys. Query with `'*'` unless you mean a specific strand; if you need strict
strand equality, filter the returned keys on `get_value().get_strand()`.

::::

::::{tab-item} {{ py_tab }}
:sync: py

```python
import pygenogrove as pg

g = pg.Grove(100)
g.insert("chr1", pg.GenomicCoordinate("+", 100, 200), "gene1")
g.insert("chr1", pg.GenomicCoordinate("+", 150, 250), "gene2")
g.insert("chr1", pg.GenomicCoordinate("+", 300, 400), "gene3")
g.insert("chr2", pg.GenomicCoordinate("+", 100, 200), "gene4")

# One index (chromosome) — the usual, faster form
for key in g.intersect(pg.GenomicCoordinate("*", 175, 225), "chr1"):
    print(key.data, key.value)
# gene1, gene2 (gene3 does not overlap; gene4 is on chr2)

# Every index
len(g.intersect(pg.GenomicCoordinate("*", 175, 225)))     # 3
```

`intersect(query, index)` and `intersect(query)` both return a {term}`QueryResult`. Overlap is
strand-aware: two coordinates overlap when their ranges share a base and their strands are equal
**or either one is `'*'`**. A `'*'` query matches any strand, a `'+'` query matches stored `'+'`
and `'*'` keys, and a `'.'` query matches stored `'.'` and `'*'` keys. Query with `'*'` unless you
mean a specific strand; if you need strict strand equality, filter the returned keys on
`key.value.strand`.

::::

:::::

## Working with results

A query returns the matching **{term}`key handles <key>`** — the same handles inserts return — so a
result can be fed straight into graph operations, removal, or {term}`payload` edits.

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

`intersect` returns a `gdt::query_result<key_type, data_type>`. Its `get_keys()` returns
`const std::vector<gdt::key<key_type, data_type>*>&`, a read-only reference to a vector of
{term}`pointers <pointer>` to keys owned by the grove, in tree order. Because the pointers
themselves are not {term}`const` (the keys they point to may be modified), the keys can go directly
into `add_edge` ({doc}`/guide/graph/building`) or `remove_key` ({doc}`removing`) as they are.
Continuing from above:

```cpp
auto results = my_grove.intersect(gdt::interval{175, 225}, "chr1");
const auto& keys = results.get_keys();     // keep the result alive while using the reference

if (!keys.empty()) {
    my_grove.add_edge(keys.front(), keys.back());
}
```

Bind the result to a variable before calling `get_keys()`; iterating
`my_grove.intersect(...).get_keys()` directly would dangle — point at a result object that has
already been destroyed, because the unnamed result object ends at the end of the statement. Pointers stay valid until the key is removed and
the grove compacted ({doc}`removing`). Never modify a key's coordinate through them (see
{doc}`inserting`).

::::

::::{tab-item} {{ py_tab }}
:sync: py

`intersect` returns a `QueryResult`, which is {term}`iterable <iterator / iterable>` but not a
list:

- `len(result)` — number of hits
- iterating it (a `for` loop) yields the matching `Key`s in tree order
- `result.keys` — the same keys as a list
- `result.query` — the query coordinate you passed

Continuing from above:

```python
result = g.intersect(pg.GenomicCoordinate("*", 175, 225), "chr1")
len(result)                       # 2
hits = list(result)               # [Key(+:100-200), Key(+:150-250)]
g.add_edge(hits[0], hits[1])      # handles go straight into graph operations
```

Each `Key` keeps the grove alive and stays valid until `compact()` is called ({doc}`removing`).
`key.value` is a copy, so reading it back is always safe.

::::

:::::

## Nearest neighbours (`flanking`)

Where `intersect` finds what covers a region, `flanking` finds the closest keys on **either side**
of it that do **not** overlap it: the *predecessor* (nearest before) and the *successor* (nearest
after). Typical use: the upstream and downstream genes of an enhancer.

Keys that overlap the query are excluded. Among the rest, the predecessor is the key whose end is
closest below the query's start and the successor the key whose start is closest above the query's
end. For nested intervals this can differ from plain sort order: between `[50, 100]` and `[80, 90]`,
`[50, 100]` is the closer predecessor of `[150, 200]` even though `[80, 90]` sorts later. For
single-value ("scalar") keys (`numeric`, `kmer`) nearest-by-value and sort order coincide. The distance itself is left to you,
because it depends on the key type: for closed intervals it is `query.start - predecessor.end - 1`.

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

With the includes and aliases from the first example on this page:

```cpp
gst::grove<gdt::interval, std::string> g(100);
g.insert_data("chr1", gdt::interval{100, 200}, "A", gst::sorted);
g.insert_data("chr1", gdt::interval{500, 600}, "B", gst::sorted);
g.insert_data("chr1", gdt::interval{900, 1000}, "C", gst::sorted);

auto r = g.flanking(gdt::interval{650, 700}, "chr1");

if (auto* pred = r.get_predecessor()) {
    // "B" — largest non-overlapping key below the query
}
if (auto* succ = r.get_successor()) {
    // "C" — smallest non-overlapping key above the query
}
```

`flanking(const key_type& query, std::string_view index)` returns a
`gdt::flanking_query_result<key_type, data_type>`. Either pointer is `nullptr` (a null pointer,
which the `if (auto* pred = ...)` form above tests for) when no such key exists (query past the
last key, or an unknown index). The pointers are ordinary key handles and stay valid as long as the
key is not removed.

::::

::::{tab-item} {{ py_tab }}
:sync: py

```python
import pygenogrove as pg

g = pg.Grove(100)
g.insert_sorted("chr1", pg.GenomicCoordinate("+", 100, 200), "A")
g.insert_sorted("chr1", pg.GenomicCoordinate("+", 500, 600), "B")
g.insert_sorted("chr1", pg.GenomicCoordinate("+", 900, 1000), "C")

r = g.flanking(pg.GenomicCoordinate("*", 650, 700), "chr1")
r.predecessor.data      # 'B' — nearest non-overlapping key before the query
r.successor.data        # 'C' — nearest non-overlapping key after the query
```

`flanking(query, index)` returns a `FlankingResult` with `predecessor` and `successor`, each a `Key`
or `None` when no such key exists (query past the last key, or an unknown index). The keys are
ordinary `Key` handles, with the same lifetime rules as above.

::::

:::::

## Filtering flanking candidates

A second form of `flanking` takes a {term}`predicate` `is_compatible(candidate, query)` — a
function returning true or false — that is applied to each candidate before the overlap and
ordering checks. Use it for constraints the key type does not encode — most commonly, "nearest
neighbour on the same strand". The predicate only removes candidates from the answer; it does not
make the search faster, because the search still visits the same parts of the tree and filters
afterwards.

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

With the aliases from above plus `#include <genogrove/data_type/genomic_coordinate.hpp>`:

```cpp
// grove keyed by genomic_coordinate, which carries the strand
gst::grove<gdt::genomic_coordinate, std::string> grove(100);
grove.insert_data("chr1", gdt::genomic_coordinate{'+', 100, 200}, "A");
grove.insert_data("chr1", gdt::genomic_coordinate{'-', 300, 400}, "B");   // opposite strand, but nearer
gdt::genomic_coordinate q{'+', 500, 510};

auto r = grove.flanking(q, "chr1",
    [](const auto& candidate, const auto& query) {
        return query.get_strand() == '*' || candidate.get_strand() == '*'
            || candidate.get_strand() == query.get_strand();
    });
// r.get_predecessor() is "A" at [100, 200]: the '-' key "B" was skipped
```

The predicate — here a {term}`lambda`, an unnamed function written inline — receives the two **key
values** (here `genomic_coordinate`s). For plain `interval` keys there is no strand to inspect;
filter on whatever your key type exposes.

::::

::::{tab-item} {{ py_tab }}
:sync: py

```python
import pygenogrove as pg

g = pg.Grove()
g.insert("chr1", pg.GenomicCoordinate("+", 100, 200))
g.insert("chr1", pg.GenomicCoordinate("-", 300, 400))   # opposite strand, but nearer

q = pg.GenomicCoordinate("+", 500, 510)
r = g.flanking(q, "chr1", lambda cand, query: cand.strand == query.strand)
r.predecessor.value     # GenomicCoordinate('+', 100, 200) — the '-' key was skipped
```

The predicate — here a `lambda`, an unnamed function written inline — receives the two **key
values** (`GenomicCoordinate`s). {term}`Exceptions <exception>` raised inside it propagate to the
caller; this form holds the {term}`GIL` because it calls back into Python, so other Python threads
wait while it runs.

::::

:::::