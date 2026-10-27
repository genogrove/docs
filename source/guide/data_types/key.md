# Key

A **key** is what a grove actually stores: a key-type value (the coordinate the tree sorts on, see
{doc}`index`) together with an optional **data payload** (whatever you want to carry with it — a
name, a record, a JSON object). Inserts and queries hand you keys; graph edges connect keys.

## What a key holds

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

`gdt::key<key_type, data_type = void>` — the value, and a payload of type `data_type`. Leave
`data_type` out (or write `void`) for a key that is only a value.

```cpp
#include <genogrove/data_type/key.hpp>
#include <genogrove/data_type/interval.hpp>

namespace gdt = genogrove::data_type;

struct GeneInfo { std::string name; double expression; };

gdt::key<gdt::interval, GeneInfo> gene{gdt::interval{100, 200}, GeneInfo{"BRCA1", 45.3}};
gdt::key<gdt::interval>           bare{gdt::interval{100, 200}};     // no payload
```

A grove creates keys for you on insert and returns a pointer to the stored key; you rarely construct
one by hand except for `grove::insert(index, key)` on a payload-less grove.

::::

::::{tab-item} {{ py_tab }}
:sync: py

`Key` — the coordinate, and a payload. You never construct a `Key` yourself: `insert` returns one,
queries yield them, and `add_external_key` returns one for a graph-only node.

```python
import pygenogrove as pg

g = pg.Grove()
k = g.insert("chr1", pg.GenomicCoordinate("+", 100, 200), {"gene": "FOO"})
hit = list(g.intersect(pg.GenomicCoordinate("*", 150, 160), "chr1"))[0]   # also a Key
```

`BedKey`, `GffKey`, `NumericKey` and `KmerKey` are the same thing for the typed and point groves.

::::

:::::

## Reading and changing a key

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

```cpp
gene.get_value().to_string();        // "[100, 200]"  — the coordinate
gene.get_data().name;                // "BRCA1"       — the payload (const or mutable reference)
gene.get_data().expression = 50.0;   // edit the payload in place
gene.set_data(GeneInfo{"TP53", 32.1});
gene.to_string();                    // "[100, 200]"  — delegates to the value
```

Methods:

- `get_value()` — `const key_type&`
- `set_value(v)` — replace the value. **Never call this on a key a grove holds**: the tree is
  ordered by the value (see {doc}`index`)
- `get_data()` — `const data_type&` on a const key, `data_type&` otherwise; `set_data(d)` — replace
  the payload. Both exist only when `data_type` is not `void`
- `has_data()` — `constexpr bool`, `true` iff `data_type` is not `void`
- `to_string()` — the value's text form
- `serialize(os)`, `static deserialize(is)` — binary persistence of value and payload (what
  `grove::serialize` uses); the payload type must be serializable (see
  {doc}`/guide/serialization`)
- `operator==`, `operator<`, `operator>` — see below

::::

::::{tab-item} {{ py_tab }}
:sync: py

```python
k.value          # GenomicCoordinate('+', 100, 200) — a copy
k.data           # {'gene': 'FOO'}
str(k)           # "+:100-200"
repr(k)          # "Key(+:100-200)"
```

Attributes:

- `value` — the coordinate, returned **by copy**, so editing it cannot disturb the grove
- `data` — the payload. On `Grove` / `NumericGrove` / `KmerGrove` it is your JSON value, decoded
  afresh on **each** access, so `k.data["x"] = 1` does not stick — build a new payload if you need
  to change it. On `BedGrove` / `GffGrove` it is the live `BedEntry` / `GffEntry`, and editing it in
  place is fine (the payload is not part of the tree order)

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
gdt::key<gdt::interval, std::string> a{gdt::interval{100, 200}, "gene1"};
gdt::key<gdt::interval, std::string> b{gdt::interval{100, 200}, "gene2"};
gdt::key<gdt::interval, std::string> c{gdt::interval{100, 300}, "gene1"};

a == b;    // true  — same interval, payload ignored
a != c;    // true  — auto-generated from operator==
a <  c;    // true  — ordered by the interval
```

`operator==` requires the key type to be `std::equality_comparable`; `<` and `>` are always
available because `key_type_base` requires them. C++20 does not derive `<=` / `>=` from these; spell
them `!(a > b)` / `!(a < b)` if needed. There is no `std::hash<key>`; hash the value if you need to
(`std::hash<gdt::genomic_coordinate>{}(k.get_value())`).

::::

::::{tab-item} {{ py_tab }}
:sync: py

```python
hits = list(g.intersect(pg.GenomicCoordinate("*", 0, 10**6), "chr1"))
unique_coords = set(hits)      # one entry per distinct coordinate — payloads ignored
hits[0] == k                   # True if same coordinate, whatever the payloads
```

`==`, `<`, `>` and `hash()` all delegate to `value`. `hash(k)` is the C++ `std::hash` of the
value, so it agrees with `hash(k.value)`. (`<=` / `>=` are not defined on `Key`; they are on the
coordinate types.)

::::

:::::

## Lifetime

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

A grove owns its keys in storage with stable addresses, so a `key*` from an insert or a query stays
valid until the key is removed **and** the grove is compacted (see {doc}`/guide/grove/removing`).
A key you construct yourself is an ordinary value: copyable, movable, destroyed with its scope.

A key without a payload costs nothing extra: `sizeof(gdt::key<gdt::interval>) ==
sizeof(gdt::interval)`.

::::

::::{tab-item} {{ py_tab }}
:sync: py

A `Key` keeps its owning grove alive for as long as you hold it, so the grove cannot disappear
underneath it. It stays valid until the grove is **compacted**: `grove.compact()` rebuilds the key
storage and invalidates every indexed key — rediscover them with a fresh query (see
{doc}`/guide/grove/removing`); keys from `add_external_key` are unaffected. A `Key` cannot be
pickled or moved to another grove.

::::

:::::