# Removing Keys

Removing a {term}`key` unlinks it from its tree and drops every graph {term}`edge` that touched it,
but it does **not** free the key's storage slot (the place in the grove's memory where the key
lives): the grove keeps slots in place so that the {term}`handles <key>` of all *other* keys stay
valid. When many removals have accumulated, `compact()` ({term}`compact`) rebuilds the storage and
reclaims the dead slots — at the cost of invalidating every indexed key handle you still hold.

## Removing a key

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

`remove_key(index, key)` takes the {term}`index` name and a key handle (from an insert or a query).
It returns `true` if the key was found and removed, `false` otherwise (unknown index, null
{term}`pointer`, or a key not in that index's tree). With the includes and aliases from
{doc}`inserting`:

```cpp
gst::grove<gdt::interval, std::string> my_grove(100);
auto* k = my_grove.insert_data("chr1", gdt::interval{100, 200}, "gene1", gst::sorted);

bool removed = my_grove.remove_key("chr1", k);   // true

// Typical use: prune by a property of the payload
// (coverage_of() and min_coverage stand for your own function and threshold)
auto results = my_grove.intersect(gdt::interval{0, 1000000}, "chr1");
for (auto* key : results.get_keys()) {
    if (coverage_of(key) < min_coverage) {
        my_grove.remove_key("chr1", key);
    }
}
```

Removing while looping over the result is safe: the result holds its own list of handles, and
removing one key does not invalidate the others.

The tree rebalances itself (a {term}`node` left too empty borrows from a neighbour or merges with
it, repeating upwards as needed, and a root with a single child is collapsed), and all incoming and
outgoing graph edges of the key are dropped, so there is no need to call `remove_edge` /
`remove_all_edges` ({doc}`/guide/graph/editing`) first. The key stays in the grove's storage as a
dead slot.

::::

::::{tab-item} {{ py_tab }}
:sync: py

`remove_key(index, key)` takes the index name and a `Key` (from an insert or a query). It returns
`True` if the key was found and removed, `False` otherwise (unknown index, `None`, or a key not in
that index's tree).

```python
import pygenogrove as pg

g = pg.Grove(100)
k = g.insert("chr1", pg.GenomicCoordinate("+", 100, 200), {"coverage": 3})

g.remove_key("chr1", k)        # True

# Typical use: prune by a property of the payload
for key in g.intersect(pg.GenomicCoordinate("*", 0, 10**6), "chr1"):
    if key.data["coverage"] < 5:
        g.remove_key("chr1", key)
```

Removing while looping over the result is safe: the result holds its own list of handles, and
removing one key does not invalidate the others.

The tree rebalances itself and every graph edge touching the key is dropped, so there is no need to
call `remove_all_edges` first. The key stays in the grove's storage as a dead slot. `remove_key`
{term}`releases the GIL <GIL>`, so other Python threads keep running while it works.

::::

:::::

## Reclaiming storage (`compact`)

`compact()` rebuilds the key storage so it holds exactly the live keys, remapping the graph edges to
the moved keys. It is O(N + E) — its cost grows with the number of keys plus the number of edges —
and runs only when you call it.

:::{warning}
`compact()` **invalidates every indexed key handle** obtained earlier from inserts, queries or graph
navigation. Call it only when no code still holds such a handle, and rediscover keys through a fresh
query afterwards. Handles of **{term}`external <external key>`** (graph-only) keys are unaffected.
:::

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

Continuing from above (`std::cout` needs `#include <iostream>`; `my_grove` is the grove from the
removal example, after many inserts and removals):

```cpp
// ... many insert / remove cycles ...

std::cout << "Live indexed keys: " << my_grove.indexed_vertex_count() << "\n";
std::cout << "Storage slots:     " << my_grove.key_storage_size()     << "\n";

if (my_grove.key_storage_size() > 2 * my_grove.indexed_vertex_count()) {
    my_grove.compact();   // all key pointers from before this line are now dangling (invalid)
}
```

`key_storage_size()` also counts the internal separator keys a {term}`B+ tree` needs (the signpost
keys in its internal nodes that route a search), so it is larger than `indexed_vertex_count()` even
without removals as soon as a tree has internal nodes; compaction pays off once removed keys
dominate the difference. ("Vertex" is the graph word for a key: `indexed_vertex_count()` counts the
keys the trees hold.)

::::

::::{tab-item} {{ py_tab }}
:sync: py

```python
import pygenogrove as pg

g = pg.Grove()
k = g.insert("chr1", pg.GenomicCoordinate(".", 100, 200))
g.remove_key("chr1", k)        # True — edges to/from k are also removed
g.key_storage_size()           # still counts the dead slot

g.compact()                    # reclaims it; k and every other indexed Key are now invalid

for key in g.intersect(pg.GenomicCoordinate("*", 0, 10**6), "chr1"):
    ...                        # fresh, valid handles
```

`key_storage_size()` also counts the internal separator keys a B+ tree needs (the signpost keys in
its internal nodes that route a search), so it is larger than `indexed_vertex_count()` even
without removals as soon as a tree has internal nodes; compaction pays off once removed keys
dominate the difference. `compact()`
releases the GIL.

::::

:::::

## Counting what is stored

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

- `indexed_vertex_count()` — keys in the B+ trees (what `intersect` can find)
- `external_vertex_count()` — graph-only keys added with `add_external_key`
- `vertex_count()` — the two together
- `key_storage_size()` — storage slots in use: live keys + separator keys + dead slots

::::

::::{tab-item} {{ py_tab }}
:sync: py

- `len(g)` / `size()` / `indexed_vertex_count()` — keys in the B+ trees (what `intersect` can find)
- `external_vertex_count()` — graph-only keys added with `add_external_key`
- `vertex_count()` — the two together
- `key_storage_size()` — storage slots in use: live keys + separator keys + dead slots

::::

:::::