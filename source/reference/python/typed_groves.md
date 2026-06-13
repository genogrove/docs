# Typed groves (BED / GFF)

The schemaless {doc}`grove` is the everyday tool. The **typed** groves
`BedGrove` (`grove<genomic_coordinate, bed_entry>`) and `GffGrove`
(`grove<genomic_coordinate, gff_entry>`) are the alternative for when you want a
**guaranteed BED/GFF schema** and full interop with typed C++ `.gg` files: instead
of a JSON payload, each key carries a structured `BedEntry` / `GffEntry`.

Both are genomic-coordinate keyed and expose the same surface as `Grove`
(multi-index `insert` / `intersect`, the graph overlay, `serialize` /
`deserialize`), with the differences noted below.

## BedGrove

```python
import pygenogrove as pg

g = pg.BedGrove(100)

# insert(index, coord, data) — the GenomicCoordinate is the key, BedEntry is the payload
entry = pg.BedEntry("chr1", 1000, 2000)   # BED-native coords (0-based, half-open)
entry.name = "BRCA1"
entry.score = 900
entry.strand = "+"
key = g.insert("chr1", pg.GenomicCoordinate(".", 1000, 1999), entry)

print(key.value.start, key.data.name)     # 1000 BRCA1

for hit in g.intersect(pg.GenomicCoordinate(".", 1500, 1600), "chr1"):
    print(hit.data.name, hit.data.score)

g.serialize("genes.gg")
reloaded = pg.BedGrove.deserialize("genes.gg")   # preserves the BedEntry data
```

Differences from the universal `Grove`:

- `insert(index: str, key: GenomicCoordinate, data: BedEntry) -> BedKey` takes the
  BED payload.
- `add_external_key(key: GenomicCoordinate, data: BedEntry) -> BedKey` takes the
  payload too.
- Typed groves keep **unlabelled** graph edges (for binary C++ interop), so the
  labelled-edge methods (`add_edge(s, t, data)`, `get_edges`, `get_neighbors_if`,
  `link_with`) are **absent**. Plain edges and all edge-cleanup methods are
  present — see {doc}`graph`.

`GffGrove` is identical with a `GffEntry` payload.

### Entry-deriving inserts

The foolproof way to load records from a reader — pass a bare entry and the
`GenomicCoordinate` key is derived from its native coordinates (no
hand-conversion):

- `insert(index, entry) -> BedKey` — a 2-argument overload. BED's half-open
  `[s, e)` → closed `[s, e-1]`; GFF's 1-based `[s, e]` → `[s-1, e-1]`. Strand is
  taken from the record's strand column (absent → `'.'`).
- `insert_bulk(index, entries, presorted=False) -> list[BedKey]` — same idea for a
  whole list of bare entries.

```python
g = pg.BedGrove(256)
for e in pg.BedReader("peaks.bed"):
    g.insert(e.chrom, e)        # key derived from each entry
```

### Fast-path inserts

Data-carrying groves also expose explicit fast paths:

- `insert_sorted(index, coord, data) -> BedKey` — single insert on the
  rightmost-append path (skips tree traversal).
- `insert_bulk(index, items, presorted=False) -> list[BedKey]` — insert many
  explicit `(GenomicCoordinate, BedEntry)` records at once (10–20× faster for
  large datasets; an empty index is built bottom-up in O(n)). `presorted=True`
  skips the internal sort.

:::{warning}
**Precondition:** sorted/bulk inserts require ascending intervals, and when
appending to a non-empty index every new interval must be greater than all
existing ones. Violating this corrupts B+ tree ordering — use plain `insert` if
unsure.
:::

### BedKey

Like `Key`, but adds a `data` attribute:

- `value` — the interval, returned **by copy** (do not rely on mutating it).
- `data` — the associated `BedEntry`, a **live, mutable** reference. Unlike
  `value`, the payload is not part of the B+ tree ordering, so editing it in place
  is safe.

`BedQueryResult` is the `BedGrove` analog of `QueryResult` (its keys are `BedKey`s).

## BedEntry

A single BED record. Coordinates are BED-native: 0-based, half-open
`[start, end)` (distinct from the closed `[start, end]` of the `GenomicCoordinate`
key).

```python
BedEntry(chrom: str, start: int, end: int)
```

**Attributes** (read/write):

- `chrom` (str), `start` (int), `end` (int)
- `name` — `Optional[str]` (BED4+)
- `score` — `Optional[int]` (BED5+)
- `strand` — `Optional[str]`, a single character (`'+'`, `'-'`, `'.'`). Assigning
  an empty or multi-character string raises `ValueError`; `None` clears it (BED6+).
- `thickness` — `Optional[ThickInfo]` (BED7+)
- `item_rgb` — `Optional[RgbColor]` (BED9+)
- `blocks` — `Optional[BlockInfo]` (BED12)

Supporting value types: `ThickInfo(start, end)`, `RgbColor(red, green, blue)`
(channels 0–255), and `BlockInfo(count, sizes, starts)` (with `list[int]`
`sizes`/`starts`). List fields are returned/assigned by copy.

## GffGrove

The same typed grove for **GFF3/GTF** records — identical surface to `BedGrove`,
with a `GffEntry` payload:

```python
import pygenogrove as pg

g = pg.GffGrove(100)

entry = pg.GffEntry("chr1", 1000, 2000, "gene")   # GFF-native coords (1-based, inclusive)
entry.source = "ensembl"
entry.strand = "+"
entry.attributes = {"gene_id": "ENSG1", "gene_name": "BRCA1"}
key = g.insert("chr1", pg.GenomicCoordinate(".", 999, 1999), entry)

print(key.data.type, key.data.get_gene_id())      # gene ENSG1

g.serialize("genes.gg")
reloaded = pg.GffGrove.deserialize("genes.gg")
```

`GffKey` mirrors `BedKey` (`value` is a copy, `data` is a live mutable `GffEntry`
reference); `GffQueryResult` is the `GffGrove` analog of `QueryResult`.

## GffEntry

A single GFF3/GTF record. Coordinates are GFF-native: **1-based, both endpoints
inclusive**.

```python
GffEntry(seqid: str, start: int, end: int, type: str)
```

**Attributes** (read/write):

- `seqid` (str), `source` (str), `type` (str), `start` (int), `end` (int)
- `score` — `Optional[float]`
- `strand` — `Optional[str]`, a single character (`'+'`, `'-'`, `'.'`, `'?'`);
  empty or multi-character raises `ValueError`, `None` clears it.
- `phase` — `Optional[int]` (CDS phase 0/1/2)
- `attributes` — `dict[str, str]`, the column-9 key/value pairs (returned/assigned
  by copy)
- `format` — a `GffFormat` enum (`GFF3` / `GTF` / `UNKNOWN`)

**Methods**: `is_gtf()`, `is_gff3()`, `get_attribute(key)`, and the GTF helpers
`get_gene_id()`, `get_transcript_id()`, `get_exon_number()`, `get_gene_name()`,
`get_gene_biotype()` (each returns `None` when the attribute is absent).