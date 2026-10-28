# Intervals and Genomic Coordinates

The two region {term}`key types <key type>`. Both are {term}`0-based closed` `[start, end]` (see
{doc}`index` for the conversion from file coordinates). `genomic_coordinate` adds a {term}`strand`
and makes {term}`overlap` strand-aware; `interval` is the strand-less version and exists in C++ only.

## Building a region

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

```cpp
#include <genogrove/data_type/interval.hpp>
#include <genogrove/data_type/genomic_coordinate.hpp>

namespace gdt = genogrove::data_type;

gdt::interval           iv{100, 200};            // [100, 200], no strand
gdt::genomic_coordinate gc{'+', 1000, 2000};     // + strand, [1000, 2000]
gdt::genomic_coordinate un{'.', 1000, 2000};     // unstranded value
gdt::genomic_coordinate wild{'*', 1000, 2000};   // wildcard strand (for queries)
```

Both constructors throw a `std::invalid_argument` {term}`exception` if `start > end`;
`genomic_coordinate` also throws for a strand other than `'+'`, `'-'`, `'.'`, `'*'`. A
default-constructed `interval` (`gdt::interval{}`, no arguments) is a "not set" placeholder. Both
fields hold the *sentinel* `interval::INVALID_POSITION`, a reserved value (`SIZE_MAX`, the largest
value a `size_t` can hold). Use it only as a placeholder. A default-constructed `genomic_coordinate`
is the real value `'.'`, `[0, 0]`, not a sentinel.

::::

::::{tab-item} {{ py_tab }}
:sync: py

```python
import pygenogrove as pg

gc   = pg.GenomicCoordinate("+", 1000, 2000)    # + strand, [1000, 2000]
un   = pg.GenomicCoordinate(".", 1000, 2000)    # unstranded value
wild = pg.GenomicCoordinate("*", 1000, 2000)    # wildcard strand (for queries)
```

Signature (for reference, not to paste):

```python
GenomicCoordinate(strand: str, start: int, end: int)
```

Raises a `ValueError` {term}`exception` if `start > end` or the strand is not one of `'+'`, `'-'`,
`'.'`, `'*'`, and `TypeError` for a negative coordinate. `GenomicCoordinate()` with no arguments is the real value
`'.'`, `[0, 0]`.

::::

:::::

## Strand semantics

| Strand | Meaning |
|---|---|
| `'+'` | forward strand |
| `'-'` | reverse strand |
| `'.'` | a **concrete unstranded** value — matches only `'.'` |
| `'*'` | a **wildcard** — matches any strand |

Two coordinates overlap when their ranges share at least one base **and** their strands are
compatible: equal, or either one is `'*'`. The `'.'` / `'*'` distinction is the usual surprise:
`'.'` is a real strand value that only matches other `'.'` coordinates, while `'*'` matches
everything. Store unstranded features as `'.'`; query with `'*'` when strand should be ignored.

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

```cpp
// continuing from above: the includes and the gdt alias
gdt::genomic_coordinate plus {'+', 100, 200};
gdt::genomic_coordinate minus{'-', 100, 200};
gdt::genomic_coordinate dot  {'.', 100, 200};
gdt::genomic_coordinate star {'*', 150, 160};

gdt::genomic_coordinate::overlaps(plus, minus);   // false — different strands
gdt::genomic_coordinate::overlaps(plus, dot);     // false — '.' matches only '.'
gdt::genomic_coordinate::overlaps(plus, star);    // true  — '*' matches anything
gdt::interval::overlaps({100, 200}, {150, 250});  // true  — intervals have no strand
```

The comments show what each call returns; the lines compute the value without printing it, so wrap
a call in `std::cout << std::boolalpha << ... << '\n';` to see it. In a grove the same rule applies:
after inserting `plus` and `minus`, a query with strand `'+'` finds only `plus` and a query with
`'*'` finds both (see {doc}`/guide/grove/querying`).

::::

::::{tab-item} {{ py_tab }}
:sync: py

```python
import pygenogrove as pg

plus  = pg.GenomicCoordinate("+", 100, 200)
minus = pg.GenomicCoordinate("-", 100, 200)
dot   = pg.GenomicCoordinate(".", 100, 200)
star  = pg.GenomicCoordinate("*", 150, 160)

pg.GenomicCoordinate.overlaps(plus, minus)   # False — different strands
pg.GenomicCoordinate.overlaps(plus, dot)     # False — '.' matches only '.'
pg.GenomicCoordinate.overlaps(plus, star)    # True  — '*' matches anything

g = pg.Grove(100)
g.insert("chr1", plus)                       # the payload is optional
g.insert("chr1", minus)
len(g.intersect(pg.GenomicCoordinate("+", 150, 160), "chr1"))   # 1
len(g.intersect(pg.GenomicCoordinate("*", 150, 160), "chr1"))   # 2
```

The comments show what each line evaluates to; in an interactive Python session each line prints its
result. `"chr1"` is the {term}`index` — the chromosome tree a key goes into; `insert` takes it first
and `intersect` last (see {doc}`/guide/grove/querying`).

::::

:::::

## Ordering

Keys sort **coordinate-first**: by `start`, then `end`, then strand in the order `* < . < + < -`.
`interval` sorts by `start`, then `end`. Equality compares all fields.

## The interval type

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

`gdt::interval` — two `size_t` fields (unsigned integers, so positions are never negative).

Methods:

- `get_start()`, `get_end()` — the bounds
- `set_range(start, end)` — set both at once; throws `std::invalid_argument` if `start > end`
- `static overlaps(a, b)` — ranges share at least one base
- `static aggregate(a, b)` — the bounding interval `[min(start), max(end)]`
- `to_string()` — `"[100,200]"`
- `serialize(os)`, `static deserialize(is)` — binary persistence ({term}`serialization`);
  `deserialize` throws `std::invalid_argument` if the stored `start > end`
- `INVALID_POSITION` — `static constexpr size_t` (a compile-time constant), the default-constructed
  sentinel

`interval` has no `std::hash` specialisation. `std::hash` is the standard function that computes an
integer from a value (a {term}`hash`); unordered containers use that integer to place and find the
value (see {doc}`index`). Without one, an `interval` cannot be a {term}`registry` key or an unordered
container key, unless you write a hash of your own.

::::

::::{tab-item} {{ py_tab }}
:sync: py

Python has no separate interval class: a region without strand is already covered by
`GenomicCoordinate('.', start, end)`. `Grove`, `BedGrove` and `GffGrove` are all keyed by
`GenomicCoordinate`.

::::

:::::

## The genomic coordinate type

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

`gdt::genomic_coordinate` — a `char` strand (one character) and two `std::size_t` bounds.

Methods:

- `get_strand()`, `get_start()`, `get_end()` — the fields
- `set_strand(c)` — throws `std::invalid_argument` for a strand outside `+ - . *`
- `set_range(start, end)` — set both bounds; throws `std::invalid_argument` if `start > end`
- `static overlaps(a, b)` — range overlap **and** strand compatibility (see above)
- `static aggregate(a, b)` — the bounding coordinate
- `to_string()` — `"+:100-200"`
- `serialize(os)`, `static deserialize(is)` — binary persistence
- `std::hash<genomic_coordinate>` — specialised, so it works in unordered containers and as a
  `registry` key

::::

::::{tab-item} {{ py_tab }}
:sync: py

`GenomicCoordinate` — attributes `strand`, `start`, `end` (read-only).

Methods:

- `set_strand(c)` — `ValueError` for a strand outside `+ - . *`
- `set_range(start, end)` — set both bounds; `ValueError` if `start > end`
- `GenomicCoordinate.overlaps(a, b)` — static; range overlap **and** strand compatibility
- `<`, `<=`, `>`, `>=`, `==`, `hash()`, `str()`, `repr()` — ordering as above; `str(gc)` is
  `"+:100-200"`

The attributes are read-only so a stored key cannot be changed by accident; the two setters are for
values you have **not** inserted yet (see {doc}`index`).

::::

:::::