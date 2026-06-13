# Grove

The universal `Grove` is `grove<genomic_coordinate, json>`: a B+ tree keyed by
{doc}`coordinates` that stores any JSON-serializable payload (dict / list /
scalar / `None`) per key. Each key may carry a **different** shape — no schema is
enforced.

```python
Grove(order: int = 3)
```

- `order` — maximum branching factor (max keys per node = `order - 1`). Minimum 3.
  Higher orders (100–500) reduce tree height for large datasets.

Groves support **multiple indices** (typically one per chromosome): the first
argument to `insert` / `intersect` selects the index.

## Inserting and querying

```python
import pygenogrove as pg

g = pg.Grove()
g.insert("chr1", pg.GenomicCoordinate("+", 100, 200), {"gene": "FOO"})
g.insert("chr1", pg.GenomicCoordinate(".", 300, 400))   # no payload -> None

hit = list(g.intersect(pg.GenomicCoordinate("+", 150, 160), "chr1"))[0]
hit.value, hit.data        # GenomicCoordinate('+', 100, 200), {'gene': 'FOO'}
```

**Methods**:

- `insert(index: str, key: GenomicCoordinate, data=None) -> Key` — insert a
  coordinate with an optional JSON-serializable payload at the given index.
- `intersect(query: GenomicCoordinate) -> QueryResult` — strand-aware overlaps
  across **all** indices.
- `intersect(query: GenomicCoordinate, index: str) -> QueryResult` — overlaps in
  a **specific** index (faster; prefer this when you know the chromosome).
- `len(grove)` / `size()` / `indexed_vertex_count()` — number of indexed
  intervals across all indices.
- `get_order()` — the tree's branching factor.

## Key

A `Key` is a wrapper for a coordinate stored in the grove. It is returned by
inserts and yielded by query results, and it keeps its owning `Grove` alive.

**Attributes**:

- `value` — the `GenomicCoordinate`, returned **by copy** (mutating it cannot
  corrupt ordering).
- `data` — the payload. On the universal `Grove` this is the JSON value you
  stored, returned as a freshly decoded copy on each access.

:::{note}
`Key` objects are only valid while their owning `Grove` is alive. The bindings
keep the `Grove` alive for as long as you hold a `Key`, but keys cannot be
pickled or carried across groves.
:::

## QueryResult

The object returned by `intersect`.

**Attributes**: `query` (the query coordinate), `keys` (the matching keys).

**Methods**: `__len__()` (number of results), `__iter__()` (iterate the keys).

## Flanking (nearest neighbours)

`flanking` finds the nearest **non-overlapping** keys on either side of a query.

```python
flanking(query: GenomicCoordinate, index: str) -> FlankingResult
```

**FlankingResult**:

- `predecessor` — the closest key entirely **before** the query (a `Key`), or `None`.
- `successor` — the closest key entirely **after** the query (a `Key`), or `None`.

Keys overlapping the query are excluded; for nested intervals the predecessor is
the one with the largest end (smallest gap). Compute a gap distance from the
returned key, e.g. `query.start - result.predecessor.value.end - 1` (closed
coordinates).

### Predicate-filtered flanking

A third argument filters candidates with a Python callable
`is_compatible(candidate, query) -> bool` applied at each leaf candidate; only
keys for which it returns `True` are considered. The headline use is the nearest
neighbour **on the same strand**:

```python
import pygenogrove as pg
g = pg.Grove()
g.insert("chr1", pg.GenomicCoordinate("+", 100, 200))
g.insert("chr1", pg.GenomicCoordinate("-", 300, 400))   # opposite strand, nearer

q = pg.GenomicCoordinate("+", 500, 510)
# Without the predicate, the nearer '-' key would be the predecessor.
# A same-strand predicate skips it -> nearest '+' neighbour:
r = g.flanking(q, "chr1", lambda cand, q: cand.strand == q.strand)
r.predecessor.value         # GenomicCoordinate('+', 100, 200)
```

- The predicate receives the key **values** (e.g. `GenomicCoordinate`); for the
  typed groves it receives the interval value.
- Predicate exceptions propagate to Python; the call holds the GIL.

## Removal and storage

- `remove_key(index: str, key: Key) -> bool` — remove a key from the index's B+
  tree (rebalancing as needed) and drop every graph edge touching it. Returns
  `True` if found; a `None` key or unknown index returns `False`. The key remains
  as a **dead storage slot** until `compact()`.
- `compact() -> None` — reclaim the dead slots left by `remove_key()`.
- `vertex_count()` — indexed + external keys.
- `external_vertex_count()` — external keys only (see {doc}`graph`).
- `key_storage_size()` — total storage slots (live + B+ tree separators + dead slots).

:::{warning}
**`compact()` invalidates indexed `Key` handles.** It moves key storage, so every
previously-returned indexed `Key` (from `insert` / `insert_bulk` / `intersect` /
`flanking`) becomes invalid and must not be used afterward — re-discover keys via
a fresh query. Keys from `add_external_key()` are unaffected.
:::

```python
import pygenogrove as pg
g = pg.Grove()
k = g.insert("chr1", pg.GenomicCoordinate(".", 100, 200))
g.remove_key("chr1", k)        # True; edges to/from k are also removed
g.key_storage_size()           # still counts the dead slot
g.compact()                    # reclaims it — k (and all old indexed Keys) now invalid
# Re-query to get fresh, valid handles:
for key in g.intersect(pg.GenomicCoordinate("*", 0, 10**6), "chr1"):
    ...
```

## Serialization

Groves persist to a zlib-compressed `.gg` binary.

- `serialize(path: str)` — write the grove (coordinates + payloads + graph
  overlay) to `path`.
- `deserialize(path: str) -> Grove` *(static)* — load a grove written by `serialize`.

```python
g.serialize("out.gg")
reloaded = pg.Grove.deserialize("out.gg")
```

An edgeless universal-`Grove` `.gg` stores its payload as **JSON text**, so it is
readable by a C++ `grove<genomic_coordinate, std::string>`. With labelled edges
(see {doc}`graph`) the C++ interop type is
`grove<genomic_coordinate, std::string, std::string>`.