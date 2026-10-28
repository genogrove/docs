# Grove

A **{term}`grove`** is the central data structure of {term}`genogrove`: a {term}`B+ tree` (a
sorted, balanced search tree) that stores genomic intervals and answers {term}`overlap` queries.
One grove holds one tree **per {term}`index`** — in practice one per chromosome — so a query for
`chr1` only touches `chr1`'s tree. Every stored item is a **{term}`key`**: a coordinate value (the
thing the tree sorts and searches on) plus an optional **data {term}`payload`** you attach to it.
On top of the trees sits an optional **{term}`graph overlay`** that lets you link keys with directed
{term}`edges <edge>`.

This page explains the model and how to create a grove. The subpages cover each operation:

- {doc}`inserting` — single, sorted and bulk inserts, keys without data, {term}`key handles <key>`
- {doc}`querying` — overlap queries, working with results, nearest-neighbour ({term}`flanking`) queries
- {doc}`removing` — removing keys and reclaiming storage
- {doc}`custom_key_types` — using your own type as the key (C++)
- {doc}`loading_data` — filling a grove from BED, GFF/GTF and BAM files
- {doc}`/guide/graph/index` — the graph overlay

Persisting a grove to disk is covered in the {doc}`serialization guide </guide/serialization/index>`.

## What a grove stores

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

A grove is a class {term}`template` with three parameters, filled in when you declare a grove:

```cpp
gst::grove<key_type, data_type = void, edge_data_type = void>
```

- `key_type` — the coordinate type the tree sorts and searches on (the {term}`key type`). Four
  built-in types are provided (see {doc}`../data_types/index`): `interval` ({term}`0-based closed`
  `[start, end]`), `genomic_coordinate` (the same plus a {term}`strand`), `numeric` (a single
  integer) and `kmer` (a DNA {term}`k-mer`). Any type satisfying the `key_type_base` concept (a
  compile-time checklist of the operations a key type must provide) works — see
  {doc}`custom_key_types`.
- `data_type` — the payload attached to each key, e.g. `std::string`, a struct, or a file-reader
  record such as `gio::bed_entry`. Leave it out (`void`) for a grove that stores coordinates only.
- `edge_data_type` — the {term}`edge metadata` carried by graph edges. Leave it out (`void`) for
  plain edges.

Pick `genomic_coordinate` when features on opposite strands must not overlap each other; pick
`interval` when strand is irrelevant.

::::

::::{tab-item} {{ py_tab }}
:sync: py

{term}`pygenogrove` ships a small family of ready-made groves; the C++ type parameters are fixed
per class:

| Class | Key type | Payload | Use it for |
|---|---|---|---|
| `Grove` | `GenomicCoordinate` | any JSON value, or `None` | the everyday choice |
| `BedGrove` / `GffGrove` | `GenomicCoordinate` | `BedEntry` / `GffEntry` | a guaranteed BED/GFF record per key, or reading a C++ `.gg` with a `bed_entry` / `gff_entry` payload — see {doc}`loading_data` |
| `NumericGrove` / `KmerGrove` | `Numeric` / `Kmer` | any JSON value, or `None` | integer or k-mer keys instead of genomic coordinates |

**Start with `Grove`.** Its payload is any JSON-serializable value (dict / list / scalar / `None`),
and each key may carry a different shape — no schema is enforced. Payloads must be **finite**:
`float('nan')`, `float('inf')` or `float('-inf')` at any nesting depth raise `ValueError` at insert
time. The same rule applies to edge metadata and to `Registry` payloads.

The point-key groves (whose keys are a single value rather than a range) offer the same methods as
`Grove` with their own key types:

```python
import pygenogrove as pg

g = pg.NumericGrove()
g.insert("ids", pg.Numeric(42), {"label": "answer"})
list(g.intersect(pg.Numeric(42), "ids"))[0].data   # {'label': 'answer'}

km = pg.KmerGrove()
km.insert("seqs", pg.Kmer("ACGT"), {"count": 3})
```

::::

:::::

## Creating a grove

The only constructor argument is the tree **{term}`order`**: the maximum number of children per
{term}`node` (and `order - 1` keys). It must be at least 3. **100 is a good default**; read the
{doc}`performance guide </guide/performance>` before tuning it.

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

```cpp
#include <genogrove/structure/grove/grove.hpp>
#include <genogrove/data_type/interval.hpp>
#include <genogrove/data_type/genomic_coordinate.hpp>

namespace gdt = genogrove::data_type;
namespace gst = genogrove::structure;

int main() {
    // Intervals with a string payload
    gst::grove<gdt::interval, std::string> grove1(100);

    // Stranded coordinates with a string payload
    gst::grove<gdt::genomic_coordinate, std::string> grove2(100);

    // Created with no argument: the order defaults to 3
    gst::grove<gdt::interval, std::string> grove3;

    return 0;
}
```

An order below 3 throws the {term}`exception` `std::invalid_argument("grove order must be >= 3")`:
with order 2, splitting a full internal node would leave its new sibling with zero keys, which a
B+ tree forbids.

::::

::::{tab-item} {{ py_tab }}
:sync: py

```python
import pygenogrove as pg

g = pg.Grove()          # order 3 (the default)
g = pg.Grove(100)       # order 100
```

```python
Grove(order: int = 3)
```

Already covered: `Grove` keys are always strand-aware `GenomicCoordinate`s, like `grove2` in the C++
tab, so there is no second key type to choose here.

An order below 3 raises `ValueError` (with order 2, splitting a full internal node would leave its
new sibling with zero keys, which a B+ tree forbids). `get_order()` returns the order a grove was built
with.

::::

:::::

## Indices

Every insert and every query names an **index**, normally the chromosome. Each index is its own B+
tree, created automatically on the first insert that names it. Querying a single index is faster
than querying all of them, so pass the chromosome whenever you know it.

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

The index is the first argument of `insert_data` and the last argument of `intersect` (a
`std::string_view`, so a string literal or a `std::string` both work). Leave the index out of
`intersect` to search every index. Continuing from `grove1` above:

```cpp
grove1.insert_data("chr1", gdt::interval{100, 200}, "FOO");
grove1.intersect(gdt::interval{150, 160}, "chr1");   // chr1 only
grove1.intersect(gdt::interval{150, 160});           // every index
```

To see which indices exist, read the index map of the grove (`std::cout` needs
`#include <iostream>`):

```cpp
const auto& roots = grove1.get_root_nodes();   // maps each index name to its tree's root node
for (const auto& [name, root] : roots) {
    std::cout << name << "\n";                  // chr1, chr2, ... (in no particular order)
}

if (auto it = roots.find("chr1"); it != roots.end()) {
    // it->second is the root node for chr1
}
```

The map is returned by **{term}`const` reference** — you may read it but not change it — so use
`.find()` / `.at()` to look a name up, not `operator[]`, which would try to insert a missing name
and does not compile on a read-only map. The reference is valid only while the grove is alive and
unmodified. Indices cannot be created by hand; they appear on first insertion.

::::

::::{tab-item} {{ py_tab }}
:sync: py

The index is the first argument of `insert` and the second argument of `intersect`:

```python
import pygenogrove as pg

g = pg.Grove(100)
g.insert("chr1", pg.GenomicCoordinate("+", 100, 200), "FOO")
g.intersect(pg.GenomicCoordinate("*", 150, 160), "chr1")   # chr1 only
g.intersect(pg.GenomicCoordinate("*", 150, 160))           # every index
```

Indices cannot be created by hand; they appear on first insertion. Already covered:
the C++ index listing is `get_index_names()` on the on-disk reader `GroveView` in Python (see
{doc}`/guide/serialization/partial_reading`), and for an in-memory `Grove` you keep the names you
insert.

::::

:::::

## Ownership and lifetime

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

`grove` (and its internal `node` type) is **non-copyable and move-only**: you cannot make a second
copy of a grove, only hand the existing one over (move it) or refer to it. Copying is deleted
because the grove owns raw {term}`pointers <pointer>`; a shallow copy would double-free (both copies
would try to release the same memory). Move it or pass it by reference:

```cpp
// OK — move construction (in: an open std::ifstream, see the serialization guide)
auto loaded = gst::grove<gdt::interval, std::string>::deserialize(in);

// OK — pass by reference
void process(gst::grove<gdt::interval, std::string>& g);

// OK — move into a container (my_grove: a grove created as above)
std::vector<gst::grove<gdt::interval, std::string>> groves;
groves.push_back(std::move(my_grove));

// ERROR — copy is deleted
// auto copy = my_grove;
// void f(gst::grove<gdt::interval, std::string> g);   // pass-by-value copies
```

The key pointers a grove hands out (from inserts and queries) point into storage the grove owns.
They stay valid until `compact()` ({term}`compact`) is called, which invalidates every indexed key
pointer — see {doc}`removing`.

::::

::::{tab-item} {{ py_tab }}
:sync: py

A `Grove` is an ordinary Python object. The `Key` objects it hands out (from inserts and queries)
keep their owning `Grove` alive for as long as you hold them, so a key never outlives its grove.
Keys cannot be pickled (saved with Python's `pickle` module) or moved to another grove.

Indexed keys become invalid after `compact()` — see {doc}`removing`.

::::

:::::

```{toctree}
:maxdepth: 1
:hidden:

inserting
querying
removing
custom_key_types
loading_data
```