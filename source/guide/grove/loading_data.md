# Loading Data from Files

Combine the {doc}`file readers </guide/io/index>` with grove insertion to load genomic data directly
from BED, GFF/GTF, and BAM/SAM files. The readers open plain and gzip/BGZF-compressed (`.gz`) files
alike.

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

The readers live in the `genogrove::io` namespace. Each is walked with a `for` loop, one record at
a time. A reader throws the {term}`exception` `std::runtime_error` when the file cannot be opened
(from its constructor) or a line cannot be parsed (during the loop), so each example creates the
reader inside the `try` block and prints the error instead of crashing.

### BED Files

#### Simple Loading (Incremental Insertion)

```cpp
#include <genogrove/io/bed_reader.hpp>
#include <genogrove/structure/grove/grove.hpp>
#include <genogrove/data_type/interval.hpp>
#include <iostream>

namespace gio = genogrove::io;
namespace gdt = genogrove::data_type;
namespace gst = genogrove::structure;

int main() {
    gst::grove<gdt::interval, std::string> my_grove(100);

    // Read and insert each entry
    try {
        gio::bed_reader reader("genes.bed.gz");
        for (const auto& entry : reader) {
            // gst::sorted promises the file is sorted by position within each chromosome;
            // drop it if yours is not (sort -k1,1 -k2,2n). Convert half-open [start, end)
            // to closed [start, end - 1]
            // The name column is optional in BED: fall back to "unknown" when absent
            my_grove.insert_data(entry.chrom,
                                gdt::interval(entry.start, entry.end - 1),
                                entry.name.value_or("unknown"),
                                gst::sorted);
        }
    } catch (const std::runtime_error& e) {
        std::cerr << "Error: " << e.what() << "\n";
    }

    std::cout << "Loaded " << my_grove.indexed_vertex_count() << " intervals\n";

    // Query the loaded data
    auto results = my_grove.intersect(gdt::interval{1000, 2000}, "chr1");
    std::cout << "Found " << results.get_keys().size() << " overlapping intervals\n";

    return 0;
}
```

#### Efficient Loading (Bulk Insertion)

For large files (>10K intervals), use {term}`bulk insertion <bulk insert>` for better performance:

```cpp
#include <genogrove/io/bed_reader.hpp>
#include <genogrove/structure/grove/grove.hpp>
#include <genogrove/data_type/interval.hpp>
#include <iostream>
#include <map>
#include <vector>

namespace gio = genogrove::io;
namespace gdt = genogrove::data_type;
namespace gst = genogrove::structure;

int main() {
    gst::grove<gdt::interval, std::string> my_grove(100);

    // Group entries by chromosome: one list of (interval, name) pairs per chromosome name
    std::map<std::string, std::vector<std::pair<gdt::interval, std::string>>> data;

    try {
        gio::bed_reader reader("large_dataset.bed.gz");
        for (const auto& entry : reader) {
            // data[chrom] is that chromosome's list (created on first use);
            // emplace_back builds one (interval, name) pair at the end of the list
            data[entry.chrom].emplace_back(
                gdt::interval(entry.start, entry.end - 1),
                entry.name.value_or("unknown"));
        }
    } catch (const std::runtime_error& e) {
        std::cerr << "Error: " << e.what() << "\n";
    }

    // Bulk insert per chromosome (data must be sorted).
    // Each map entry is a (name, list) pair; [chrom, chrom_data] gives both parts a name.
    for (auto& [chrom, chrom_data] : data) {
        my_grove.insert_data(chrom, chrom_data, gst::sorted, gst::bulk);
    }

    std::cout << "Loaded " << my_grove.indexed_vertex_count() << " intervals using bulk insertion\n";

    return 0;
}
```

### GFF/GTF Files

```cpp
#include <genogrove/io/gff_reader.hpp>
#include <genogrove/structure/grove/grove.hpp>
#include <genogrove/data_type/interval.hpp>
#include <iostream>

namespace gio = genogrove::io;
namespace gdt = genogrove::data_type;
namespace gst = genogrove::structure;

int main() {
    gst::grove<gdt::interval, std::string> my_grove(100);

    try {
        gio::gff_reader reader("annotations.gff.gz");
        for (const auto& entry : reader) {
            // Keep gene features that carry a gene_id; the ID is the payload
            // (get_gene_id() returns an optional: `!gene_id` means the attribute is absent)
            auto gene_id = entry.get_gene_id();
            if (entry.type != "gene" || !gene_id) continue;

            // GFF coordinates are 1-based inclusive — shift both to the grove's 0-based closed keys
            my_grove.insert_data(entry.seqid,
                                gdt::interval(entry.start - 1, entry.end - 1),
                                *gene_id,
                                gst::sorted);
        }
    } catch (const std::runtime_error& e) {
        std::cerr << "Error: " << e.what() << "\n";
    }

    std::cout << "Loaded " << my_grove.indexed_vertex_count() << " features\n";

    return 0;
}
```

### BAM/SAM Files

```cpp
#include <genogrove/io/bam_reader.hpp>
#include <genogrove/structure/grove/grove.hpp>
#include <genogrove/data_type/interval.hpp>
#include <iostream>

namespace gio = genogrove::io;
namespace gdt = genogrove::data_type;
namespace gst = genogrove::structure;

int main() {
    gst::grove<gdt::interval, std::string> my_grove(100);

    // Read only high-quality primary alignments (mapping quality >= 20)
    gio::bam_reader_options opts = gio::bam_reader_options::primary_only();
    opts.min_mapq = 20;
    try {
        gio::bam_reader reader("alignments.bam", opts);
        for (const auto& entry : reader) {
            my_grove.insert_data(entry.chrom,
                                 gdt::interval(entry.start, entry.end - 1),
                                 entry.qname, gst::sorted);
        }
    } catch (const std::runtime_error& e) {
        std::cerr << "Error: " << e.what() << "\n";
    }

    std::cout << "Loaded " << my_grove.indexed_vertex_count() << " reads\n";

    return 0;
}
```

### Key Points

- BED and BAM readers produce 0-based half-open `[start, end)` coordinates — subtract 1 from `end` when constructing `gdt::interval`
- GFF/GTF readers produce 1-based inclusive `[start, end]` coordinates — subtract 1 from both `start` and `end` so BED- and GFF-derived keys share the grove's {term}`0-based closed` space
- File readers handle decompression automatically
- For small files, use incremental insertion with the `sorted` tag (a {term}`sorted insert`; see {doc}`inserting`)
- For large files (>10K intervals), collect data and use bulk insertion with the `sorted` tag
- Data must be sorted before using bulk insertion: sort the file first (`sort -k1,1 -k2,2n`) unless you know it is; on unsorted input the tag silently produces wrong query results
- Bulk insertion is ~10-20x faster for large datasets
- See the {doc}`performance guide </guide/performance>` for detailed insertion strategies

::::

::::{tab-item} {{ py_tab }}
:sync: py

The schemaless {doc}`Grove <./index>` (any JSON {term}`payload`, no fixed layout) is the everyday
tool. The **typed** groves `BedGrove` (the C++ `grove<genomic_coordinate, bed_entry>`) and
`GffGrove` (`grove<genomic_coordinate, gff_entry>`) are the alternative for when you want a
**guaranteed BED/GFF schema** — every key carries exactly one record — and full interoperability
with typed C++ {term}`.gg files <.gg file>`: instead of a JSON payload, each key carries a
structured `BedEntry` / `GffEntry`.

Both are genomic-coordinate keyed and offer the same methods as `Grove` (multi-index `insert` /
`intersect`, the {term}`graph overlay`, `serialize` / `deserialize`), with the differences noted
below. Like the C++ readers, `BedReader` and `GffReader` open plain and gzip/BGZF-compressed (`.gz`)
files alike — see {doc}`/guide/io/index`.

### BedGrove

```python
import pygenogrove as pg

g = pg.BedGrove(100)

# insert(index, coord, data) — the GenomicCoordinate is the key, BedEntry is the payload
entry = pg.BedEntry("chr1", 1000, 2000)   # BED-native coords (0-based, half-open)
entry.name = "BRCA1"
entry.score = 900
entry.strand = "+"
# the key's strand is chosen by you here; use the record's strand so strand-aware queries behave
key = g.insert("chr1", pg.GenomicCoordinate("+", 1000, 1999), entry)

print(key.value.start, key.data.name)     # 1000 BRCA1

for hit in g.intersect(pg.GenomicCoordinate("*", 1500, 1600), "chr1"):   # "*" = any strand
    print(hit.data.name, hit.data.score)

g.serialize("genes.gg")
reloaded = pg.BedGrove.deserialize("genes.gg")   # preserves the BedEntry data
```

Differences from the universal `Grove`:

- `insert(index: str, key: GenomicCoordinate, data: BedEntry) -> BedKey` takes the
  BED payload.
- `add_external_key(key: GenomicCoordinate, data: BedEntry) -> BedKey` takes the
  payload too.
- Typed groves keep **unlabelled** graph edges — edges without {term}`edge metadata`, so their
  files stay readable by C++. Edges themselves work; only the methods that read or write edge
  metadata are absent — see {doc}`/guide/graph/index`.

`GffGrove` is identical with a `GffEntry` payload.

#### Entry-deriving inserts

The foolproof way to load records from a reader — pass a bare entry and the
`GenomicCoordinate` key is derived from its native coordinates (no
hand-conversion):

- `insert(index, entry) -> BedKey` — a 2-argument {term}`overload`. BED's half-open
  `[s, e)` → closed `[s, e-1]`; GFF's 1-based `[s, e]` → `[s-1, e-1]`. Strand is
  taken from the record's strand column (absent → `'.'`).
- `insert_bulk(index, entries, presorted=False) -> list[BedKey]` — same idea for a
  whole list of bare entries.

A complete example follows under *Loading from a reader* below.

#### Fast-path inserts

Data-carrying groves also expose the explicit fast paths of {doc}`inserting`:
`insert_sorted(index, interval, data) -> BedKey` and
`insert_bulk(index, items, presorted=False) -> list[BedKey]`, which takes explicit
`(GenomicCoordinate, BedEntry)` records.

:::{warning}
The same precondition applies as for the universal `Grove`: sorted and bulk inserts require
ascending intervals, and appending to a non-empty index requires every new interval to be greater
than all existing ones. This is not checked; breaking it silently corrupts the tree. Use plain
`insert` if unsure.
:::

#### BedKey

Like the universal `Key`, but its `data` is a typed `BedEntry` instead of a JSON value:

- `value` — the interval, returned **by copy** (do not rely on mutating it).
- `data` — the associated `BedEntry`, a **live, mutable** reference (the universal `Grove` returns
  a fresh copy each time). Unlike `value`, the payload is not part of the B+ tree ordering, so
  editing it in place is safe.

`BedQueryResult` is the `BedGrove` analog of `QueryResult` (its keys are `BedKey`s).

### BedEntry

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

### GffGrove

The same typed grove for **GFF3/GTF** records — identical surface to `BedGrove`,
with a `GffEntry` payload:

```python
import pygenogrove as pg

g = pg.GffGrove(100)

entry = pg.GffEntry("chr1", 1000, 2000, "gene")   # GFF-native coords (1-based, inclusive)
entry.source = "ensembl"
entry.strand = "+"
entry.attributes = {"gene_id": "ENSG1", "gene_name": "BRCA1"}
key = g.insert("chr1", pg.GenomicCoordinate("+", 999, 1999), entry)   # [start - 1, end - 1]

print(key.data.type, key.data.get_gene_id())      # gene ENSG1

g.serialize("genes.gg")
reloaded = pg.GffGrove.deserialize("genes.gg")
```

`GffKey` mirrors `BedKey` (`value` is a copy, `data` is a live mutable `GffEntry`
reference); `GffQueryResult` is the `GffGrove` analog of `QueryResult`.

### GffEntry

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
- `format` — a `GffFormat` enum, i.e. one of a fixed set of named values (`GFF3` / `GTF` /
  `UNKNOWN`)

**Methods**: `is_gtf()`, `is_gff3()`, `get_attribute(key)`, and the GTF helpers
`get_gene_id()`, `get_transcript_id()`, `get_exon_number()`, `get_gene_name()`,
`get_gene_biotype()` (each returns `None` when the attribute is absent).

### Loading from a reader

`BedReader` and `GffReader` are {term}`iterable <iterator / iterable>`: a `for` loop walks a BED or
GFF3/GTF file one record at a time, yielding `BedEntry` / `GffEntry` records. A file that cannot be
opened raises `RuntimeError` when the reader is created; a line that cannot be parsed raises it
during the loop. BAM files are read the same way with `BamReader` — see {doc}`/guide/io/bam`. The
2-argument
`insert` derives the grove's 0-based closed `GenomicCoordinate` key from each entry's
native coordinates, so you never hand-convert:

```python
import pygenogrove as pg

# load a file into a typed grove
g = pg.BedGrove(256)
for e in pg.BedReader("peaks.bed"):
    g.insert(e.chrom, e)

gff = pg.GffGrove(256)
for e in pg.GffReader("genes.gff3"):
    gff.insert(e.seqid, e)

# bulk-load one chromosome at a time (insert_bulk is per-index):
# the list comprehension keeps only the chr1 records
g2 = pg.BedGrove(256)
g2.insert_bulk("chr1", [e for e in pg.BedReader("peaks.bed") if e.chrom == "chr1"])
```

::::

:::::