# Key

A {term}`grove` stores keys. A {term}`key` has two parts. The **value** is the coordinate that the
tree sorts on (a {term}`key type`, see {doc}`index`). The optional {term}`payload` is whatever you
want to carry with it: a name, a record, a JSON object. Inserts and queries hand you keys, and graph
{term}`edges <edge>` connect keys. On this page *value* means the coordinate and *key* means the
stored item that wraps it.

## What a key holds

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

`gdt::key<key_type, data_type = void>` — a {term}`template`: the value, and a payload of type
`data_type`. Leave `data_type` out (or write `void`, "no type") for a key that is only a value.

```cpp
#include <genogrove/data_type/key.hpp>
#include <genogrove/data_type/interval.hpp>
#include <string>

namespace gdt = genogrove::data_type;

struct GeneInfo { std::string name; double expression; };   // a plain record type for the payload

gdt::key<gdt::interval, GeneInfo> gene{gdt::interval{100, 200}, GeneInfo{"BRCA1", 45.3}};
gdt::key<gdt::interval>           bare{gdt::interval{300, 400}};     // no payload
```

A grove creates keys for you on insert and returns a {term}`pointer` to the stored key (its
{term}`key handle`). `insert_data(index, value, data)` builds the key for you. You construct a key by
hand only for `grove::insert(index, key)` on a payload-less grove.

::::

::::{tab-item} {{ py_tab }}
:sync: py

`Key` — the coordinate, and a payload; it is the {term}`key handle` through which you reach a stored
key. You never construct a `Key` yourself: `insert` returns one, queries yield them, and
`add_external_key` returns one for a graph-only node (an {term}`external key`).

```python
import pygenogrove as pg

g = pg.Grove()
k = g.insert("chr1", pg.GenomicCoordinate("+", 100, 200), {"name": "BRCA1", "expression": 45.3})   # "chr1" is the index
bare = g.insert("chr1", pg.GenomicCoordinate("+", 300, 400))   # no payload (the payload is optional)
hit = list(g.intersect(pg.GenomicCoordinate("*", 150, 160), "chr1"))[0]   # also a Key
```

`"chr1"` is the {term}`index` (the chromosome tree) and the dict the payload. `intersect` returns a
{term}`QueryResult`, hence the `list(...)`.

The two tabs differ on purpose in two places. C++ stores the `GeneInfo` record as it is; Python
stores the payload as a JSON value, so the example wraps it in a dict. The C++ example uses an
`interval`; Python has no `interval` class, so the example uses a `GenomicCoordinate` (the C++
`genomic_coordinate`).

`BedKey` and `GffKey` are the same thing for `BedGrove` and `GffGrove`, whose payload is a `BedEntry`
or `GffEntry` record (see {doc}`/guide/grove/loading_data`). `NumericKey` and `KmerKey` are the same
thing for `NumericGrove` and `KmerGrove`.

::::

:::::

## Reading and changing a key

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

```cpp
// continuing from above: gene is the key built in the first block
gene.get_value().to_string();        // "[100,200]"   — the coordinate
gene.get_data().name;                // "BRCA1"       — the payload (const or mutable reference)
gene.get_data().expression = 50.0;   // edit the payload in place
gene.set_data(GeneInfo{"TP53", 32.1});
gene.to_string();                    // "[100,200]"   — delegates to the value (Python spells this `str(k)`)
```

C++ has no `repr`; `to_string()` is the text form. `get_data()` hands you the stored payload itself (a {term}`const` — read-only — reference on a
read-only key, an editable one otherwise), so edits through it stick. (In Python's `Grove` the
payload comes back as a decoded copy instead; see the Python tab.)

Methods:

- `get_value()` — `const key_type&`
- `set_value(v)` — replace the value. **Never call this on a key a grove holds**: the tree is
  ordered by the value (see {doc}`index`)
- `get_data()` — `const data_type&` on a const key, `data_type&` otherwise; `set_data(d)` — replace
  the payload. Both exist only when `data_type` is not `void`
- `has_data()` — `constexpr bool` (a compile-time constant), `true` exactly when `data_type` is not
  `void`
- `to_string()` — the value's text form
- `serialize(os)`, `static deserialize(is)` — binary persistence ({term}`serialization`) of value and
  payload (what `grove::serialize` uses); the payload type must be serializable (see
  {doc}`/guide/serialization/index`)
- `operator==`, `operator<`, `operator>` — see below

::::

::::{tab-item} {{ py_tab }}
:sync: py

```python
# continuing from above: k is the Key returned by insert in the first block
k.value          # GenomicCoordinate('+', 100, 200) — a copy
k.data["name"]   # "BRCA1"       — the payload (a decoded copy)
k.data["expression"] = 50.0   # no effect: each access decodes a fresh copy, so edits do not stick
str(k)           # "+:100-200"   — delegates to the value
repr(k)          # "Key(+:100-200)"
```

Already covered: C++ `set_data(d)` replaces the payload in place. On `Grove` you choose the payload at
`insert`, and the payload of a `BedKey` or `GffKey` is editable in place (see below).

Attributes:

- `value` — the coordinate, returned **by copy**, so editing it cannot disturb the grove
- `data` — the payload. On `Grove` / `NumericGrove` / `KmerGrove` it is your JSON value, decoded
  afresh on **each** access, so `k.data["x"] = 1` does not stick — build a new payload if you need to
  change it. (This differs from C++, where `get_data()` is the stored payload itself and edits stick.)
  On `BedGrove` / `GffGrove` it is the live `BedEntry` / `GffEntry`, and editing it in place is fine
  (the payload is not part of the tree order)

Methods:

- `==`, `<`, `>`, `hash()`, `str()`, `repr()` — see below

There is no way to change a stored key's **value** from Python, by design.

::::

:::::

## Comparison and hashing

Keys compare by **value only**; the payload is ignored. That is the tree's notion of identity, and
it means a payload type never has to be comparable. Two keys of the **same key class** with equal
coordinates are equal even if they come from different groves or carry different payloads. (Keys of
different classes — a C++ `key<interval, std::string>` versus a `key<interval, int>`, or a Python
`Key` versus a `BedKey` — are different types and are not compared with each other.)

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

```cpp
// continuing from above: the includes and the gdt alias
gdt::key<gdt::interval, std::string> a{gdt::interval{100, 200}, "gene1"};
gdt::key<gdt::interval, std::string> b{gdt::interval{100, 200}, "gene2"};
gdt::key<gdt::interval, std::string> c{gdt::interval{100, 300}, "gene1"};

a == b;    // true  — same interval, payload ignored
a != c;    // true  — auto-generated from operator==
a <  c;    // true  — ordered by the interval
```

The comments show what each line evaluates to; the lines compute the value without printing it.
`operator==` requires the key type to be `std::equality_comparable` (a C++20 concept: the type has
`==`); `<` and `>` are always available because `key_type_base` requires them. C++20 does not derive
`<=` / `>=` from these; spell them `!(a > b)` / `!(a < b)` if needed. There is no `std::hash<key>`: the
standard {term}`hash` function, which computes the integer that unordered containers use to place
and find a value, is not defined for `key` (see {doc}`index`). Hash the value if you need a hash:

```cpp
#include <genogrove/data_type/genomic_coordinate.hpp>
#include <functional>

gdt::key<gdt::genomic_coordinate, std::string> k{gdt::genomic_coordinate{'+', 100, 200}, "gene1"};
std::size_t h = std::hash<gdt::genomic_coordinate>{}(k.get_value());   // hash of the coordinate
```

::::

::::{tab-item} {{ py_tab }}
:sync: py

```python
# continuing from above: pg (this block builds its own grove)
g = pg.Grove(100)
a = g.insert("chr1", pg.GenomicCoordinate("+", 100, 200), {"name": "gene1"})
b = g.insert("chr1", pg.GenomicCoordinate("+", 100, 200), {"name": "gene2"})
c = g.insert("chr1", pg.GenomicCoordinate("+", 100, 300), {"name": "gene1"})

a == b    # True  — same coordinate, payload ignored
a != c    # True  — derived from ==
a <  c    # True  — ordered by the coordinate
hash(a) == hash(a.value)   # True — the hash is the coordinate's hash
```

Already covered: the C++ `std::hash<genomic_coordinate>{}(k.get_value())` is `hash(k)` in Python.

`==`, `<`, `>` and `hash()` (the integer that `set` and `dict` use to place and find a value) all delegate to
`value`. `hash(k)` is the same number as `hash(k.value)`. (`<=` / `>=` are not defined on `Key`; they are on the
coordinate types.)

::::

:::::

## Lifetime

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

A grove owns its keys in storage with stable addresses, so a `key*` from an insert or a query stays
valid until the grove is **compacted**: `compact()` ({term}`compact`) rebuilds the storage and
invalidates every indexed key pointer, whether or not that key was removed (see {doc}`/guide/grove/removing`);
only pointers from `add_external_key` ({term}`external keys <external key>`) survive. A key you
construct yourself is an ordinary value: copyable, movable, destroyed with its scope (the block of
code it was declared in).

A key without a payload costs nothing extra on GCC and Clang
(`sizeof(gdt::key<gdt::interval>) == sizeof(gdt::interval)` — `sizeof` is the size in bytes — via
`[[no_unique_address]]`, an attribute that lets the compiler give an empty payload no space at all).

::::

::::{tab-item} {{ py_tab }}
:sync: py

A `Key` keeps its owning grove alive for as long as you hold it, so the grove cannot disappear
underneath it. It stays valid until the grove is **compacted**: `grove.compact()` ({term}`compact`)
rebuilds the key storage and invalidates every `Key` that came from `insert` or a query. Find them
again with a new query (see {doc}`/guide/grove/removing`); keys from `add_external_key` are
unaffected. A `Key` cannot be
pickled (saved with Python's `pickle` module) or moved to another grove.

::::

:::::