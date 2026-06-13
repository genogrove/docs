# Graph overlay

Every grove carries an embedded **graph overlay** — directed edges between keys —
on top of its spatial B+ tree index. This lets you represent feature
relationships (exon→transcript, regulatory links, …) alongside interval queries.

## Edges between keys

```python
import pygenogrove as pg

g = pg.Grove()
a = g.insert("chr1", pg.GenomicCoordinate("+", 100, 200))
b = g.insert("chr1", pg.GenomicCoordinate("+", 300, 400))
g.add_edge(a, b)
g.has_edge(a, b)            # True
g.get_neighbors(a)         # [b]
g.out_degree(a)            # 1
```

- `add_edge(source: Key, target: Key)` — add a directed edge. Raises `ValueError`
  if either key is `None`.
- `remove_edge(source: Key, target: Key) -> bool` — remove an edge; `True` if one
  was removed.
- `has_edge(source: Key, target: Key) -> bool` — test whether an edge exists.
- `get_neighbors(source: Key) -> list[Key]` — keys directly reachable from `source`.
- `out_degree(source: Key) -> int` — number of outgoing edges from `source`.
- `edge_count() -> int` — total edges in the overlay.
- `vertex_count_with_edges() -> int` — keys with at least one outgoing edge.

:::{note}
`add_edge` does **not** deduplicate — calling it twice creates parallel edges.
:::

## External keys

`add_external_key(key: GenomicCoordinate, data=None) -> Key` adds a graph-only key
that lives **outside** the B+ tree index: it participates in the graph but is
**not** returned by `intersect()`. Useful for anchoring graph nodes that are not
themselves query targets.

```python
ext = g.add_external_key(pg.GenomicCoordinate(".", 0, 0), {"label": "promoter"})
g.add_edge(ext, a)
```

External keys are **not** invalidated by `compact()` (unlike indexed keys — see
{doc}`grove`).

## Labelled edges

On the **universal `Grove`**, edges carry a JSON-serializable payload. (The typed
`BedGrove` / `GffGrove` keep unlabelled edges for binary interop, so the
labelled-edge methods below are absent there — see {doc}`typed_groves`.)

```python
import pygenogrove as pg

g = pg.Grove()
a = g.insert("chr1", pg.GenomicCoordinate("+", 100, 200))
b = g.insert("chr1", pg.GenomicCoordinate("+", 300, 400))
g.add_edge(a, b, {"type": "exon->transcript", "weight": 7})
g.get_edges(a)                                    # [{"type": ..., "weight": 7}]
g.get_neighbors_if(a, lambda m: m["weight"] > 5)  # [b]
```

- `add_edge(source, target, data)` — add an edge with a metadata payload. The
  2-argument `add_edge` attaches `None`.
- `get_edges(source: Key) -> list` — the edge payloads of `source`'s outgoing
  edges, parallel to `get_neighbors(source)`.
- `get_neighbors_if(source: Key, predicate) -> list[Key]` — target keys whose edge
  metadata satisfies `predicate(metadata)`. The predicate receives the **decoded**
  payload (edges added without a payload yield `None`, so guard for it when mixing
  labelled and unlabelled edges).
- `link_with(keys: list[Key], predicate)` — label adjacent pairs: `predicate(k1, k2)`
  returns the edge payload to attach, or `None` to skip.

A canonical example is labelling exon→transcript edges with their intron gaps via
`link_with` over a chromosome's exon keys.

## Edge cleanup and bulk linking

Available on **every** grove (universal and typed):

- `remove_edges_from(source: Key) -> int` — remove outgoing edges; returns the count.
- `remove_edges_to(target: Key) -> int` — remove incoming edges; returns the count.
- `remove_all_edges(key: Key) -> int` — remove all edges touching `key`; returns the count.
- `clear_graph()` — remove all edges (keys are left intact).
- `graph_empty() -> bool` — whether the overlay has no edges.
- `link_if(keys: list[Key], predicate)` — add an **unlabelled** edge between each
  adjacent pair `(keys[i], keys[i+1])` for which `predicate(k1, k2)` returns
  `True` (typically over the keys returned by a bulk insert).

:::{note}
**Not yet exposed:** `remove_edges_if`
([pygenogrove#33](https://github.com/genogrove/pygenogrove/issues/33)) and SIF
export `grove_to_sif`
([pygenogrove#34](https://github.com/genogrove/pygenogrove/issues/34)).
:::

## Persistence

`serialize` / `deserialize` round-trip the graph overlay along with the
coordinates and payloads. An edge-bearing universal-`Grove` `.gg` stores per-edge
JSON metadata and is read in C++ as
`grove<genomic_coordinate, std::string, std::string>` (edgeless files are
unchanged). See {doc}`grove` for the serialization API.