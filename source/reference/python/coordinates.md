# GenomicCoordinate

`GenomicCoordinate` is the standard key type for every grove. It is a **stranded**
genomic coordinate with closed `[start, end]` bounds (0-based, both endpoints
inclusive).

```python
GenomicCoordinate(strand: str, start: int, end: int)
```

`strand` is one of `'+'`, `'-'`, `'.'`, `'*'`. Overlap requires **both**
coordinate overlap **and** strand compatibility.

```python
import pygenogrove as pg

gc = pg.GenomicCoordinate("+", 100, 200)
gc.strand, gc.start, gc.end       # '+', 100, 200
str(gc)                           # "+:100-200"
```

## Strand semantics

| Strand | Meaning                                                    |
| ------ | --------------------------------------------------------- |
| `'+'`  | Forward strand                                            |
| `'-'`  | Reverse strand                                            |
| `'.'`  | A **concrete unstranded** value — matches only `'.'`      |
| `'*'`  | A **wildcard** query strand — matches any strand          |

The `'.'` vs `'*'` distinction trips people up: `'.'` is a real value that only
matches other `'.'` coordinates, whereas `'*'` is a wildcard that matches
everything. Plain unstranded intervals are just `GenomicCoordinate('.', start, end)`.

```python
import pygenogrove as pg
g = pg.Grove()
g.insert("chr1", pg.GenomicCoordinate("+", 100, 200))
g.insert("chr1", pg.GenomicCoordinate("-", 100, 200))

# strand-aware: only the '+' coordinate matches a '+' query
len(g.intersect(pg.GenomicCoordinate("+", 150, 160), "chr1"))   # 1
# a '*' wildcard query matches both strands
len(g.intersect(pg.GenomicCoordinate("*", 150, 160), "chr1"))   # 2
```

## Sorting

Sort order is **coordinate-first**: `start` → `end` → `strand`, with strand
order `* < . < + < -`.

## Attributes and methods

**Attributes** (read-only): `strand`, `start`, `end`

**Methods**:

- `set_range(start, end)` / `set_strand(strand)` — **pre-insertion only**.
- `GenomicCoordinate.overlaps(a, b)` — static, strand-aware overlap check.

:::{warning}
Do **not** mutate a coordinate after inserting it. `start`, `end`, and `strand`
are read-only, and `set_range()` / `set_strand()` must only be used on
coordinates you have **not** yet inserted (e.g. a query you want to reuse).
Mutating a stored key silently corrupts B+ tree ordering. Note that `key.value`
returns the coordinate **by copy**, so reading it back from a grove is always
safe.
:::