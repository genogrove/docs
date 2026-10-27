# Inserting Keys

Every insert names an index (the chromosome), a coordinate, and optionally a data payload. It
returns a **key handle** you can keep for graph edges or later removal. There are three ways to
insert, from simplest to fastest: one key at a time, one key at a time with a "sorted" promise, and
a whole sorted batch at once.

## Single inserts

The default insert walks the tree to find the right leaf, so it accepts keys in any order.

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

```cpp
#include <genogrove/structure/grove/grove.hpp>
#include <genogrove/data_type/interval.hpp>

namespace gdt = genogrove::data_type;
namespace gst = genogrove::structure;

int main() {
    gst::grove<gdt::interval, std::string> my_grove(100);

    // insert_data(index, key value, data) -> pointer to the stored key
    auto* key1 = my_grove.insert_data("chr1", gdt::interval{100, 200}, "gene1");
    auto* key2 = my_grove.insert_data("chr1", gdt::interval{150, 250}, "gene2");

    // A different index (chromosome) gets its own tree
    auto* key3 = my_grove.insert_data("chr2", gdt::interval{300, 400}, "gene3");

    return 0;
}
```

::::

::::{tab-item} {{ py_tab }}
:sync: py

```python
import pygenogrove as pg

g = pg.Grove(100)

# insert(index, key, data=None) -> Key
k1 = g.insert("chr1", pg.GenomicCoordinate("+", 100, 200), {"gene": "FOO"})
k2 = g.insert("chr1", pg.GenomicCoordinate(".", 300, 400))      # no payload -> data is None

# A different index (chromosome) gets its own tree
k3 = g.insert("chr2", pg.GenomicCoordinate("+", 300, 400), {"gene": "BAR"})
```

::::

:::::

## Sorted inserts

If you insert keys in ascending order — the common case when reading a position-sorted BED or
GFF file — tell the grove so. The sorted path appends to the rightmost leaf in O(1) instead of
walking the tree.

:::{warning}
"Sorted" is a **promise, not a hint**: every key inserted this way must be greater than all keys
already in that index. The sorted path appends **without checking and does not throw** — if the
promise is broken, the tree's order is silently corrupted and later overlap queries return wrong
results. When unsure, use the plain insert; it is slower but always correct.
:::

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

Pass the `gst::sorted` tag as the last argument:

```cpp
auto* key4 = my_grove.insert_data("chr1", gdt::interval{500, 600}, "gene4", gst::sorted);
```

::::

::::{tab-item} {{ py_tab }}
:sync: py

Use `insert_sorted` instead of `insert`:

```python
k4 = g.insert_sorted("chr1", pg.GenomicCoordinate("+", 500, 600), {"gene": "BAZ"})
```

::::

:::::

## Bulk inserts

For large datasets (more than roughly 10K keys per chromosome), insert a whole sorted batch at
once. On an **empty** index the tree is built bottom-up in O(n) — fully packed leaves first, then
the internal levels — which is 10–20× faster than inserting one key at a time and leaves nodes
75–90 % full instead of about 50 %. On an index that **already has keys**, the batch is appended on
the right, so every new key must be greater than every existing one.

Bulk insertion is **per index**: call it once per chromosome.

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

Pass a container of `(key value, data)` pairs with the `gst::sorted` and `gst::bulk` tags. The
container must already be sorted:

```cpp
#include <genogrove/structure/grove/grove.hpp>
#include <genogrove/data_type/interval.hpp>
#include <vector>

namespace gdt = genogrove::data_type;
namespace gst = genogrove::structure;

int main() {
    gst::grove<gdt::interval, std::string> my_grove(100);

    std::vector<std::pair<gdt::interval, std::string>> data = {
        {{100, 200}, "gene1"}, {{300, 400}, "gene2"}, {{500, 600}, "gene3"}
    };

    // Returns a vector of key pointers, one per inserted pair
    auto keys = my_grove.insert_data("chr1", data, gst::sorted, gst::bulk);

    return 0;
}
```

Appending a batch to a non-empty index whose keys are not all greater than the existing ones
throws `std::runtime_error`. The container must satisfy `std::ranges::forward_range` and
`std::ranges::sized_range`.

For loading 1M intervals into an empty index, expect roughly: plain inserts 10–20 s, sorted
inserts 2–5 s, bulk 0.5–1 s.

::::

::::{tab-item} {{ py_tab }}
:sync: py

Pass a list of `(coordinate, data)` tuples to `insert_bulk`. By default the list is sorted for you;
pass `presorted=True` to skip that when you know it is already in order:

```python
import pygenogrove as pg

g = pg.Grove(100)

items = [(pg.GenomicCoordinate("+", i * 100, i * 100 + 50), f"feature{i}")
         for i in range(1_000_000)]

keys = g.insert_bulk("chr1", items, presorted=True)   # list[Key], one per item
```

```python
insert_bulk(index: str, items: list[tuple[GenomicCoordinate, object]], presorted: bool = False) -> list[Key]
```

`insert_bulk` releases the GIL around the native build, so other Python threads keep running.
Appending a batch to a non-empty index whose keys are not all greater than the existing ones is
rejected. The typed `BedGrove` / `GffGrove` also accept a list of bare `BedEntry` / `GffEntry`
records and derive the coordinates — see {doc}`loading_data`.

::::

:::::

## Keys without data

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

Leave out the `data_type` parameter (it defaults to `void`) for a grove that stores coordinates
only. Such a grove has no `insert_data`; you insert pre-built `gdt::key<key_type>` objects with
`insert(index, key)`, and graph-only nodes with the one-argument `add_external_key(key_value)`:

```cpp
#include <genogrove/structure/grove/grove.hpp>
#include <genogrove/data_type/interval.hpp>
#include <genogrove/data_type/key.hpp>

namespace gdt = genogrove::data_type;
namespace gst = genogrove::structure;

int main() {
    gst::grove<gdt::interval> my_grove(100);        // data_type = void

    gdt::key<gdt::interval> k{gdt::interval{100, 200}};
    auto* inserted = my_grove.insert("chr1", k);   // returns key<interval>*

    auto results = my_grove.intersect(gdt::interval{150, 175}, "chr1");   // queries work as usual

    auto* enhancer = my_grove.add_external_key(gdt::interval{5000, 5500});
    my_grove.add_edge(inserted, enhancer);

    return 0;
}
```

The two APIs are mutually exclusive and enforced at compile time: `insert_data` and the two-argument
`add_external_key(key_value, data_value)` exist only when `data_type` is not `void`; the one-argument
`add_external_key(key_value)` exists only when it is.

::::

::::{tab-item} {{ py_tab }}
:sync: py

The payload is simply optional: `insert(index, key)` without a third argument stores `None` as the
data, and `add_external_key(key)` likewise. There is no separate dataless grove class.

```python
k = g.insert("chr1", pg.GenomicCoordinate("+", 100, 200))
k.data        # None
```

The typed `BedGrove` / `GffGrove` always carry a record payload (see {doc}`loading_data`).

::::

:::::

## Key handles

Every insert returns a handle to the stored key. Keep it when you plan to add graph edges or remove
the key later; otherwise you can discard it and rediscover keys through queries.

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

The handle is a raw pointer `gdt::key<key_type, data_type>*` into storage the grove owns. It stays
valid until `compact()` is called, which invalidates every indexed key pointer (see
{doc}`removing`). Read the
coordinate with `get_value()` and the payload with `get_data()`; the payload may be modified
through the pointer.

```cpp
auto* key = my_grove.insert_data("chr1", gdt::interval{100, 200}, "gene1");
key->get_value().to_string();   // "[100,200]"
key->get_data() = "renamed";    // payload is yours to change
```

:::{warning}
Never change the **coordinate** of a stored key (`key->set_value(...)`). The tree is ordered by it,
and mutating it in place silently corrupts that order. Only the data payload may be edited through a
handle.
:::

::::

::::{tab-item} {{ py_tab }}
:sync: py

The handle is a `Key` object. `key.value` returns the coordinate **by copy**, so editing that copy
cannot disturb the tree; `key.data` returns the payload (a freshly decoded copy on the universal
`Grove`, a live mutable record on `BedGrove` / `GffGrove`).

```python
k = g.insert("chr1", pg.GenomicCoordinate("+", 100, 200), {"gene": "FOO"})
k.value       # GenomicCoordinate('+', 100, 200)
k.data        # {'gene': 'FOO'}
repr(k)       # 'Key(+:100-200)'
```

`Key` supports `==`, `<`, `>` and `hash()`, delegating to `value` and ignoring `.data` — two keys with
equal coordinates compare and hash equal even from different groves, so a `set` of keys deduplicates
by coordinate. A `Key` keeps its grove alive, cannot be pickled, and is invalidated by `compact()`
(see {doc}`removing`). More in {doc}`/guide/data_types/key`.

::::

:::::