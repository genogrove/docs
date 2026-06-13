# Python API Reference

`pygenogrove` provides Python bindings for the genogrove C++ library — a B+ tree
optimized for storing and querying genomic intervals, with an embedded graph
overlay for feature relationships.

```{toctree}
:caption: Python API
:maxdepth: 2

coordinates
grove
graph
typed_groves
io
registry
```

## Installation

```bash
pip install pygenogrove
```

Building from source requires a C++20 compiler, CMake 3.15+, and Python 3.8+:

```bash
git clone --recursive https://github.com/genogrove/pygenogrove.git
cd pygenogrove
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build
```

## Quick start

The standard key is a **`GenomicCoordinate`** (stranded, 0-based closed
`[start, end]`), and the standard **`Grove`** stores any JSON-serializable
payload (dict / list / scalar / `None`) per key:

```python
import pygenogrove as pg

grove = pg.Grove()

# Insert stranded coordinates with arbitrary metadata (or no data at all)
grove.insert("chr1", pg.GenomicCoordinate("+", 100, 200), {"gene": "FOO", "score": 5})
grove.insert("chr1", pg.GenomicCoordinate("-", 100, 200), {"gene": "BAR"})
grove.insert("chr1", pg.GenomicCoordinate(".", 300, 400))   # data defaults to None

# Query is strand-aware: a '+' query matches only '+' (and '*' wildcards)
for key in grove.intersect(pg.GenomicCoordinate("+", 150, 160), "chr1"):
    print(key.value, key.data)        # GenomicCoordinate('+', 100, 200) {'gene': 'FOO', 'score': 5}

# '*' matches any strand; '.' is a concrete unstranded value (matches only '.')
len(grove.intersect(pg.GenomicCoordinate("*", 150, 160), "chr1"))   # 2

grove.serialize("out.gg")             # JSON-text payload; a C++ grove<gc, string> can read it
```

The payload round-trips transparently (no `json` import needed), and each key
may carry a **different** shape — no schema is enforced.

## Checking your version

`pygenogrove` exposes two module-level version attributes that move on
**independent cadences** — the binding package versions on its own surface
maturity, while `__genogrove_version__` advertises the bound C++ library. When
filing a bug, report **both**:

```python
import pygenogrove as pg
print(pg.__version__)             # the pygenogrove package version, e.g. "0.5.0"
print(pg.__genogrove_version__)   # the genogrove C++ library it was built against, e.g. "0.24.6"
```

## Coordinate systems

Three coordinate conventions appear in the API. Convert deliberately when
building grove keys from file records:

| Type               | Convention                   | Example for the same locus |
| ------------------ | ---------------------------- | -------------------------- |
| `GenomicCoordinate` | 0-based **closed** `[start, end]`     | `(., 1000, 1999)` |
| `BedEntry`          | 0-based **half-open** `[start, end)`  | `(chr1, 1000, 2000)` |
| `GffEntry`          | 1-based **inclusive** `[start, end]`  | `(chr1, 1001, 2000)` |

When loading records from a reader, prefer the entry-deriving inserts on the
typed groves (`g.insert(index, entry)`) — they derive the closed
`GenomicCoordinate` key from a record's native coordinates so you never
hand-convert. See {doc}`typed_groves`.