# Loading Data from Files

Combine the {doc}`file readers </guide/io/index>` with grove insertion to load genomic data directly
from BED, GFF/GTF, and BAM/SAM files. The readers open plain and gzip/BGZF-compressed (`.gz`) files
alike. Each section below loads one format; the last two cover loading large files faster and
keeping the whole file record as the payload.

## Coordinates

The readers return the coordinates of their file format. The grove keys are {term}`0-based closed`,
so every load converts:

- BED and BAM records are 0-based half-open `[start, end)`: the key is `[start, end - 1]`.
- GFF/GTF records are 1-based closed `[start, end]`: the key is `[start - 1, end - 1]`.

The C++ examples do this by hand. In Python, the typed groves `BedGrove` and `GffGrove` do it for
you when you insert a whole record (see {ref}`loading-typed-groves`).

## Loading BED files

Read each record and insert it into a grove, keyed by the chromosome name.

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

The readers live in the `genogrove::io` namespace. Each is walked with a `for` loop, one record at
a time. A reader throws the {term}`exception` `std::runtime_error` when the file cannot be opened
(from its constructor) or a line cannot be parsed (during the loop), so each example creates the
reader inside the `try` block and prints the error instead of crashing.

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
            // BED is half-open [start, end); the grove key is closed, so use end - 1.
            // gst::sorted promises that the file is sorted within each chromosome.
            // Drop it if yours is not (see "Loading large files faster" below).
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

::::

::::{tab-item} {{ py_tab }}
:sync: py

Python reads BED files into `BedGrove`, a grove whose keys carry the whole BED record. Inserting
a bare record derives the key for you: the interval `[start, end - 1]` and the strand from the
record's strand column (`'.'` when it is absent).

```python
import pygenogrove as pg

g = pg.BedGrove(100)

for e in pg.BedReader("genes.bed.gz"):
    g.insert(e.chrom, e)                 # the key is derived from the record

hits = g.intersect(pg.GenomicCoordinate("*", 1000, 2000), "chr1")
print(f"Found {len(hits)} overlapping intervals")
for hit in hits:
    print(hit.data.name, hit.value.start, hit.value.end)
```

A file that cannot be opened raises `RuntimeError` when the reader is created. A line that cannot
be parsed raises it during the loop. If you only need one field as the payload, use the universal
`Grove` and build the key yourself: `g.insert(e.chrom, pg.GenomicCoordinate(e.strand or ".", e.start,
e.end - 1), e.name)`.

::::

:::::

## Loading GFF/GTF files

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

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

::::

::::{tab-item} {{ py_tab }}
:sync: py

`GffGrove` is the same typed grove with a `GffEntry` record per key. Inserting a bare record shifts
the 1-based `[start, end]` to `[start - 1, end - 1]` for you.

```python
import pygenogrove as pg

g = pg.GffGrove(100)

for e in pg.GffReader("annotations.gff.gz"):
    if e.type == "gene" and e.get_gene_id():       # get_gene_id() is None when the attribute is absent
        g.insert(e.seqid, e)

print(f"Loaded {g.indexed_vertex_count()} features")
```

Attribute lookups and the other record fields are described in {doc}`/guide/io/gff`.

::::

:::::

## Loading BAM/SAM files

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

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

::::

::::{tab-item} {{ py_tab }}
:sync: py

There is no typed BAM grove (`SamEntry` is not serializable). Load into the universal `Grove` with
the record's `to_coordinate()` and `to_dict()`; `consumes_reference()` skips records that cover no
reference bases. Read options such as the mapping-quality filter are described in
{doc}`/guide/io/bam`.

```python
import pygenogrove as pg

g = pg.Grove(100)
for aln in pg.BamReader("alignments.bam"):
    if aln.consumes_reference():
        g.insert(aln.chrom, aln.to_coordinate(), aln.to_dict())

print(f"Loaded {g.indexed_vertex_count()} reads")
```

::::

:::::

## Loading large files faster

For files with more than about 10,000 records, the {term}`sorted insert` and the
{term}`bulk insert` of {doc}`inserting` are much faster than plain inserts: bulk insertion is
about 10 to 20 times faster. Both rely on the data being sorted, and **neither checks it**. On
unsorted input they give wrong query results and report no error. Sort the file first, by
chromosome, start and then end, because the key order compares the start and then the end:

```bash
sort -k1,1 -k2,2n -k3,3n genes.bed > genes.sorted.bed
```

Appending to an index that already holds keys also requires every new key to be greater than all
existing ones. If you do not know whether the order is right, use the plain insert. See the
{doc}`performance guide </guide/performance>` for the numbers.

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

Collect the records per chromosome, then insert each chromosome in one call with `gst::sorted` and
`gst::bulk`:

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

::::

::::{tab-item} {{ py_tab }}
:sync: py

Group the records per chromosome, then call `insert_bulk` once for each. It sorts each list for
you. Pass `presorted=True` to skip that sort when you know the list is already in order (then the
promise above applies):

```python
import pygenogrove as pg

by_chrom = {}
for e in pg.BedReader("large_dataset.bed.gz"):
    by_chrom.setdefault(e.chrom, []).append(e)       # one list of records per chromosome

g = pg.BedGrove(100)
for chrom, entries in by_chrom.items():
    g.insert_bulk(chrom, entries)

print(f"Loaded {g.indexed_vertex_count()} intervals using bulk insertion")
```

For a single key on the sorted path, `insert_sorted(index, interval, data)` takes an explicit
coordinate and record, with the same precondition.

::::

:::::

(loading-typed-groves)=
## Keeping the whole record: typed groves

The examples above store one field per key in C++ (a name or an ID) and a whole record in Python.
Both languages can do either.

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

To keep the whole record, use the record type as the payload. `gio::bed_entry` and
`gio::gff_entry` have serialization built in, so such a grove can be saved to a {term}`.gg file <.gg file>`
directly (see {doc}`/guide/serialization/index`). Inside the loop of the BED example:

```cpp
gst::grove<gdt::interval, gio::bed_entry> records(100);

// in the loop over the reader:
records.insert_data(entry.chrom, gdt::interval(entry.start, entry.end - 1), entry, gst::sorted);
```

::::

::::{tab-item} {{ py_tab }}
:sync: py

`BedGrove` (the C++ `grove<genomic_coordinate, bed_entry>`) and `GffGrove`
(`grove<genomic_coordinate, gff_entry>`) guarantee one BED or GFF record per key and stay
compatible with typed C++ {term}`.gg files <.gg file>`. The universal `Grove` is the everyday choice
when you want any JSON {term}`payload` and no fixed layout. Both offer the same methods (multi-index
`insert` and `intersect`, the {term}`graph overlay`, `serialize` and `deserialize`), with these
differences:

- `insert(index, key, data)` takes a `BedEntry` (or `GffEntry`) as the payload, and so does
  `add_external_key(key, data)`. The two-argument `insert(index, entry)` used above derives the key.
- A key's `data` is a typed record and is **live**: editing its fields in place changes what is
  stored. The universal `Grove` returns a fresh copy each time. The `value` is returned by copy;
  never edit a key's coordinate.
- The keys are `BedKey` / `GffKey` objects and query results are `BedQueryResult` /
  `GffQueryResult`; they behave like `Key` and `QueryResult`.
- Edges are **unlabelled** (no {term}`edge metadata`), so the files stay readable by C++. Edges
  work; only the methods that read or write edge metadata are absent. See
  {doc}`/guide/graph/index`.

You can also build the record yourself and choose the key. The key's strand is up to you here; use
the record's strand so that strand-aware queries behave:

```python
import pygenogrove as pg

g = pg.BedGrove(100)

entry = pg.BedEntry("chr1", 1000, 2000)       # BED coordinates: 0-based, half-open
entry.name = "BRCA1"
entry.strand = "+"
key = g.insert("chr1", pg.GenomicCoordinate("+", 1000, 1999), entry)

print(key.value.start, key.data.name)         # 1000 BRCA1

g.serialize("genes.gg")
reloaded = pg.BedGrove.deserialize("genes.gg")  # the BedEntry records are preserved
```

For a `GffEntry` the coordinates are 1-based, so the key is `[start - 1, end - 1]`. The fields of both
record types are listed in {doc}`/guide/io/bed` and {doc}`/guide/io/gff`.

::::

:::::
