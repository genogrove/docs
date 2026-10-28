# Data Types

A {term}`grove` sorts and searches on a {term}`key type`: the value that says *where* something is.
{term}`genogrove` ships four — two interval-like types for genomic regions and two point types for
exact matches — and every grove is built on exactly one of them. The {term}`payload` you attach to a
key (a name, a record, a JSON object) is a separate thing and is covered in {doc}`key`;
{term}`interning` repeated values into small IDs is covered in {doc}`registry`.

The C++ snippets in this guide are fragments. Put them in `main()` and build as in the
{doc}`/guide/quickstart`.

| Key type (C++ / Python) | What it holds | Two values "{term}`overlap`" when | Use it for |
|---|---|---|---|
| `interval` / — | {term}`0-based closed` `[start, end]` | the ranges share at least one base | regions where {term}`strand` does not matter (C++ only) |
| `genomic_coordinate` / `GenomicCoordinate` | `[start, end]` plus a strand `+ - . *` | ranges share a base **and** strands are compatible | genes, reads, peaks — anything stranded; the only region type in Python |
| `numeric` / `Numeric` | one 32-bit integer | the values are equal | ids, ranks, positions used as exact lookups |
| `kmer` / `Kmer` | a DNA sequence of up to 32 bases, packed two bits per base into one integer | the sequences are identical | {term}`k-mer` membership and counting |

Pages: {doc}`interval_coordinate`, {doc}`numeric`, {doc}`kmer`, {doc}`key`, {doc}`registry`.

## Which type to use

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

- **`genomic_coordinate`** when features on opposite strands must not count as overlapping
  (stranded annotation, reads). Query with strand `'*'` to ignore strand for one query.
- **`interval`** when strand is irrelevant and you want the smallest key: two integers, no strand.
- **`numeric`** / **`kmer`** when "overlap" means "same value": `intersect` is then an exact lookup
  and {term}`flanking` gives the nearest values on either side.

All four are plain value types (copied and passed around like integers, no {term}`pointer` needed)
in `genogrove::data_type` (alias `gdt` throughout the docs):

```cpp
#include <genogrove/data_type/interval.hpp>
#include <genogrove/data_type/genomic_coordinate.hpp>
#include <genogrove/data_type/numeric.hpp>
#include <genogrove/data_type/kmer.hpp>

namespace gdt = genogrove::data_type;

gdt::interval           iv{100, 200};           // [100, 200]
gdt::genomic_coordinate gc{'+', 100, 200};      // + strand, [100, 200]
gdt::numeric            n{42};
gdt::kmer               k{"ACGT"};
```

Your own type can be a key type too — see {doc}`/guide/grove/custom_key_types`.

::::

::::{tab-item} {{ py_tab }}
:sync: py

- **`GenomicCoordinate`** is the key type of `Grove`, `BedGrove` and `GffGrove` (the groves are
  described in {doc}`/guide/grove/index`). There is no plain
  interval class in Python: an unstranded region is `GenomicCoordinate('.', start, end)`, and a
  query that should ignore strand uses `'*'`.
- **`Numeric`** is the key type of `NumericGrove`, **`Kmer`** of `KmerGrove`: "overlap" means
  "same value", so `intersect` is an exact lookup and `flanking` gives the nearest values on either
  side.

```python
import pygenogrove as pg

gc = pg.GenomicCoordinate("+", 100, 200)     # + strand, [100, 200]
un = pg.GenomicCoordinate(".", 100, 200)     # unstranded
n  = pg.Numeric(42)
k  = pg.Kmer("ACGT")
```

The three built-in types cover every grove class pygenogrove ships; defining your own key type is a
C++ feature (see {doc}`/guide/grove/custom_key_types`).

::::

:::::

## Coordinates

Region keys are **0-based and closed**: `[100, 200]` covers bases 100 through 200 inclusive, so a
single base is `[n, n]`. The readers keep the numbers of each file format, so you convert when you
build a key from the `start` and `end` fields of a reader record:

- BED, BAM and VCF records are {term}`half-open` `[s, e)`. The key is `[s, e - 1]`.
- GFF records are 1-based and closed `[s, e]`. The key is `[s - 1, e - 1]`.

The VCF reader has already turned the 1-based `POS` of the file into a 0-based `start`. The rule
applies to the record, not to a `POS` that you read directly from a VCF file. The conversion table
and the helpers that do it for you are in the {doc}`I/O guide </guide/io/index>`.

## What every key type can do

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

The four types share one interface. The first four rows are the `key_type_base` concept (a C++20
*concept* is a named checklist of operations a type must offer) — what any key type must provide; the
last row is needed only to persist a grove:

| Operation | Meaning |
|---|---|
| `a < b`, `a > b`, `a == b` | ordering and equality (what the tree sorts by) |
| `T::overlaps(a, b)` | static; the type's own overlap rule |
| `T::aggregate(a, b)` | static; the smallest value covering both (used for the tree's internal separators — the values its inner {term}`nodes <node>` route a search by) |
| `a.to_string()` | text form, e.g. `"[100,200]"`, `"+:100-200"`, `"ACGT"` |
| `a.serialize(os)`, `T::deserialize(is)` | binary persistence ({term}`serialization`; used by `grove::serialize`; not part of the concept) |

Constructors, comparisons, getters/setters and `overlaps` are `constexpr` (the compiler may evaluate
them while compiling), so they work in compile-time contexts such as the `static_assert` checks
below. The one exception is `kmer`'s sequence constructor (`kmer{"ACGT"}`), which
parses at run time; use `kmer{encoding, k}` when you need a compile-time k-mer.

```cpp
constexpr gdt::interval region{100, 200};
static_assert(region.get_start() == 100);
static_assert(gdt::interval::overlaps(region, gdt::interval{150, 250}));
```

`genomic_coordinate`, `numeric` and `kmer` also specialise `std::hash`: a function that turns a
value into an integer (a {term}`hash`). Unordered containers such as `std::unordered_set` use that
integer to place and find values, and so does a {term}`registry`. The hash uses exactly the fields
that `operator==` compares. `interval` has no hash, so it cannot be a key of these containers. The
grove never hashes keys, so hashing is not part of `key_type_base`.

::::

::::{tab-item} {{ py_tab }}
:sync: py

The three types share one interface:

| Operation | Meaning |
|---|---|
| `a < b`, `a <= b`, `a > b`, `a >= b`, `a == b` | ordering and equality (what the tree sorts by) |
| `GenomicCoordinate.overlaps(a, b)` (likewise `Numeric`, `Kmer`) | static; the type's own overlap rule |
| `str(a)`, `repr(a)` | text form, e.g. `"+:100-200"`, `"42"`, `"ACGT"` |
| `hash(a)` | value-based, so equal values always hash equal |

(A {term}`hash` is the integer that `set` and `dict` use to place a value and find it again quickly.)
That makes all three usable as `set` members, `dict` keys and sort keys. Do not compare hash numbers
with C++ hash values: they can differ. `GenomicCoordinate` and `Numeric` have setters: do not call them on a
value while it is a `set` member or `dict` key, since the stored hash would no longer match and the
lookup fails. {term}`Serialization <serialization>` happens through the grove (`Grove.serialize`),
not on the values themselves.

::::

:::::

## Do not change a stored key's value

A grove orders its tree by key values. Changing a value *after* it has been inserted silently breaks
that order and later queries miss keys. Setters exist so you can build or reuse a value **before**
inserting it (a query object, say); never call them on something the grove already holds.

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

The {term}`key handles <key handle>` a grove returns are non-{term}`const` (not read-only), and
`key::set_value(...)` / the type setters (`set_range`, `set_strand`, `set_value`) compile fine
through them. Nothing stops you, so follow the rule: edit only the **data payload** through a
handle, never the value.

::::

::::{tab-item} {{ py_tab }}
:sync: py

`key.value` returns a **copy**, so reading a stored coordinate back and editing the copy is always
safe. `set_range` / `set_strand` / `set_value` on a coordinate you have not inserted yet are fine;
on the universal `Grove` ({doc}`/guide/grove/index`, the grove that takes any JSON payload) the key
value you inserted is copied into the grove, so there is no way to reach the stored one.

::::

:::::

```{toctree}
:maxdepth: 1
:hidden:

interval_coordinate
numeric
kmer
key
registry
```