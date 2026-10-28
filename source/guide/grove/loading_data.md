# Loading Data from Files

Combine the {doc}`file readers </guide/io/index>` with grove insertion to load genomic data directly
from BED, GFF/GTF, and BAM/SAM files. The readers open plain and gzip/BGZF-compressed (`.gz`) files
alike. Each section below loads one format; the last two cover loading large files faster and
keeping the whole file record as the payload.

A {term}`grove` is an in-memory index of genomic regions that you can search for overlaps. Each
region is a {term}`key`. Keys are stored under an {term}`index`, which here is the chromosome name.
Each key can carry a {term}`payload`, such as a gene name. Two kinds of grove appear on this page:
the *universal* `Grove` (Python) and the C++ `grove` store a payload of your choice; the *typed*
groves `BedGrove` and `GffGrove` (Python) store the whole file record (see
[Keeping the whole record](#loading-typed-groves)). The files in the examples (`genes.bed.gz`,
`annotations.gff.gz`, `alignments.bam`) stand for your own files. The
{doc}`I/O pages </guide/io/index>` give small sample files you can save and use. If you have no BED
file, save these two tab-separated lines as `genes.bed` and use that name:

```text
chr1	1000	1500	geneA
chr1	1800	2400	geneB
```

To build and run the C++ examples, see {doc}`/guide/installation`; for Python, install
`pygenogrove` as described there.

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
    // A grove with interval keys and std::string payloads (the gene name).
    // 100 is the tree order, a tuning value; copy it as it is.
    gst::grove<gdt::interval, std::string> my_grove(100);

    // Read and insert each entry
    try {
        gio::bed_reader reader("genes.bed.gz");
        for (const auto& entry : reader) {
            // BED is half-open [start, end); the grove key is closed, so use end - 1.
            // The name column is optional in BED: fall back to "unknown" when absent
            my_grove.insert_data(entry.chrom,
                                gdt::interval(entry.start, entry.end - 1),
                                entry.name.value_or("unknown"));
        }
    } catch (const std::runtime_error& e) {
        std::cerr << "Error: " << e.what() << "\n";
    }

    // indexed_vertex_count(): the number of keys stored in the grove
    std::cout << "Loaded " << my_grove.indexed_vertex_count() << " intervals\n";

    // Query the loaded data: all keys on chr1 that overlap [1000, 2000]
    auto results = my_grove.intersect(gdt::interval{1000, 2000}, "chr1");
    std::cout << "Found " << results.get_keys().size() << " overlapping intervals\n";
    for (auto* key : results.get_keys()) {
        std::cout << "  " << key->get_data() << " " << key->get_value().to_string() << "\n";
    }

    return 0;
}
```

::::

::::{tab-item} {{ py_tab }}
:sync: py

The C++ example stores the name as the payload; Python reads BED files into `BedGrove`, a grove
whose keys carry the whole BED record. Inserting
a bare record derives the key for you: the interval `[start, end - 1]` and the strand from the
record's strand column (`'.'` when it is absent).

```python
import pygenogrove as pg

g = pg.BedGrove(100)                     # 100 is the tree order, a tuning value; copy it as it is

try:
    for e in pg.BedReader("genes.bed.gz"):
        g.insert(e.chrom, e)             # the key is derived from the record
except (RuntimeError, ValueError) as err:
    print("Error:", err)

print(f"Loaded {g.indexed_vertex_count()} intervals")

# "*" means any strand; (1000, 2000) is the closed range to search on chr1
hits = g.intersect(pg.GenomicCoordinate("*", 1000, 2000), "chr1")
print(f"Found {len(hits)} overlapping intervals")
for hit in hits:                         # hit.data is the BED record, hit.value the key
    print(f"  {hit.data.name or 'unknown'} [{hit.value.start},{hit.value.end}]")
```

A file that cannot be opened raises `RuntimeError` when the reader is created. A line that cannot
be parsed raises it during the loop. A record with `end <= start` raises `ValueError` from `insert`.
`len(hits)` counts the hits, as `results.get_keys().size()` does in C++. If you only need one field
as the payload, use the universal `Grove` and build the key yourself (`e.strand or "."` means
"the strand, or `.` when the column is absent"):

```python
g = pg.Grove(100)
g.insert(e.chrom, pg.GenomicCoordinate(e.strand or ".", e.start, e.end - 1), e.name or "unknown")
```

::::

:::::

## Loading GFF/GTF files

A GTF gene line carries a `gene_id` attribute. A GFF3 gene line carries `ID` instead. The examples
below accept both, because a GFF3 file would otherwise load no genes and print no error.

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
            // Keep gene features that carry an ID; the ID is the payload.
            // GTF uses the gene_id attribute, GFF3 uses ID. Each lookup returns an optional:
            // `!id` means the attribute is absent, and `*id` reads the value.
            auto id = entry.get_gene_id();
            if (!id) id = entry.get_attribute("ID");
            if (entry.type != "gene" || !id) continue;

            // GFF coordinates are 1-based inclusive — shift both to the grove's 0-based closed keys
            my_grove.insert_data(entry.seqid,
                                gdt::interval(entry.start - 1, entry.end - 1),
                                *id);
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

The C++ example stores the gene ID as the payload; `GffGrove` is the same typed grove with a
`GffEntry` record per key. Inserting a bare record shifts the 1-based `[start, end]` to
`[start - 1, end - 1]` for you.

```python
import pygenogrove as pg

g = pg.GffGrove(100)

try:
    for e in pg.GffReader("annotations.gff.gz"):
        gene_id = e.get_gene_id() or e.get_attribute("ID")   # GTF: gene_id, GFF3: ID; None if absent
        if e.type == "gene" and gene_id:
            g.insert(e.seqid, e)
except (RuntimeError, ValueError) as err:
    print("Error:", err)

print(f"Loaded {g.indexed_vertex_count()} features")
```

A record with `start == 0` or `end < start` raises `ValueError` from `insert`. Attribute lookups and the other record fields are described in {doc}`/guide/io/gff`.

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

    // Read only high-quality primary alignments. The mapping quality (MAPQ) is a number from 0 to 255
    // that tells how sure the aligner is about the placement; keep 20 and above.
    gio::bam_reader_options opts = gio::bam_reader_options::primary_only();
    opts.min_mapq = 20;
    try {
        gio::bam_reader reader("alignments.bam", opts);
        for (const auto& entry : reader) {
            // A read whose CIGAR uses no reference bases (for example a pure soft clip, 100S)
            // has end == start, so end - 1 would be invalid. Skip such reads.
            if (!entry.consumes_reference()) continue;
            // qname is the read name; it is the payload
            my_grove.insert_data(entry.chrom,
                                 gdt::interval(entry.start, entry.end - 1),
                                 entry.qname);
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
the record's `to_coordinate()` (the key, already converted to a closed range) and `qname` (the read
name, used as the payload, as in C++; `to_dict()` gives the whole record as a dictionary instead).
`consumes_reference()` skips records that cover no reference bases. `skip_secondary=True,
skip_supplementary=True` and `min_mapq=20` match the C++ `primary_only()` and `min_mapq = 20`; see
{doc}`/guide/io/bam`. A BAM file is binary: to look at it, use `samtools view`.

```python
import pygenogrove as pg

g = pg.Grove(100)
try:
    for aln in pg.BamReader("alignments.bam", skip_secondary=True, skip_supplementary=True, min_mapq=20):
        if aln.consumes_reference():
            g.insert(aln.chrom, aln.to_coordinate(), aln.qname)
except RuntimeError as err:
    print("Error:", err)

print(f"Loaded {g.indexed_vertex_count()} reads")
```

::::

:::::

## Loading large files faster

For files with more than about 10,000 records, the {term}`sorted insert` and the
{term}`bulk insert` of {doc}`inserting` are much faster than plain inserts. The
{doc}`performance guide </guide/performance>` measures bulk insertion at about 10 to 20 times faster.
The sorted insert, and the bulk insert in its sorted form (`gst::sorted, gst::bulk` in C++,
`presorted=True` in Python), rely on the data being in key order, and **neither checks it**. On data
in the wrong order they give wrong query results and report no error. The key order is:

- **C++ `interval` keys:** start, then end.
- **Python `GenomicCoordinate` keys** (`BedGrove`, `GffGrove`, `insert_sorted`, `insert_bulk` with
  `presorted=True`): start, then end, then strand in the order `*`, `.`, `+`, `-`.

A file that is sorted by start only is not enough, because two records with the same start must also
come in order of their end. A sorted BAM file is sorted by start only. Duplicate records (the same
start and end) also break the order, because every new key must be *strictly* greater than the
previous one. For a BED file you can sort it for C++ `interval` keys like this:

```bash
sort -k1,1 -k2,2n -k3,3n genes.bed > genes.sorted.bed
```

Appending to an index that already holds keys also requires every new key to be strictly greater
than all existing ones. If you do not know whether the order is right, use the plain insert, or the
bulk insert without the sorted promise: C++ `gst::bulk` alone and Python `insert_bulk` without
`presorted` both sort the list for you. The examples below read `.bed.gz` files and use that safe
form. To compress a sorted file, run `bgzip genes.sorted.bed`, which writes
`genes.sorted.bed.gz`.

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

Collect the records per chromosome, then insert each chromosome in one call with `gst::bulk`, which
sorts the list first. If `large_dataset.bed.gz` is already sorted as described above, pass
`gst::sorted, gst::bulk` instead to skip the sort. Use an empty index (a new grove, as here): the
new keys must be strictly greater than all keys already in the index.

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

    // Bulk insert per chromosome; gst::bulk sorts each list first.
    // Each map entry is a (name, list) pair; [chrom, chrom_data] gives both parts a name.
    for (auto& [chrom, chrom_data] : data) {
        my_grove.insert_data(chrom, chrom_data, gst::bulk);
    }

    std::cout << "Loaded " << my_grove.indexed_vertex_count() << " intervals using bulk insertion\n";

    return 0;
}
```

::::

::::{tab-item} {{ py_tab }}
:sync: py

Group the (coordinate, name) pairs per chromosome, then call `insert_bulk` once for each, as in
C++. Like `gst::bulk`, `insert_bulk` sorts each list for you, by start, end and strand, so no
sorted file is needed. Use it on an empty index: the new keys must be strictly greater than all keys
already in the index, whatever the value of `presorted`.
Pass `presorted=True` only when you know the list is already in key order (then the promise above
applies, with the strand):

```python
import pygenogrove as pg

g = pg.Grove(100)

# Group entries by chromosome: one list of (coordinate, name) pairs per chromosome name
by_chrom = {}
try:
    for e in pg.BedReader("large_dataset.bed.gz"):
        coord = pg.GenomicCoordinate(e.strand or ".", e.start, e.end - 1)
        by_chrom.setdefault(e.chrom, []).append((coord, e.name or "unknown"))
except (RuntimeError, ValueError) as err:
    print("Error:", err)

for chrom, pairs in by_chrom.items():
    g.insert_bulk(chrom, pairs)

print(f"Loaded {g.indexed_vertex_count()} intervals using bulk insertion")
```

For a single key on the sorted path, `insert_sorted(index, coordinate, data)` takes an explicit
coordinate and record, with the same precondition and no check.

::::

:::::

(loading-typed-groves)=
## Keeping the whole record: typed groves

The examples above store one field per key (a name or an ID) in C++, and in Python for BAM, the
bulk example and the `Grove` alternative; the Python BED and GFF examples store a whole record.
Both languages can do either. In Python, the *typed* groves `BedGrove` and `GffGrove` keep the whole
file record. The *universal* `Grove` keeps any JSON value that you choose.

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

To keep the whole record, use the record type as the payload. `gio::bed_entry` and
`gio::gff_entry` have serialization built in, so such a grove can be saved to a {term}`.gg file <.gg file>`
directly (see {doc}`/guide/serialization/index`). The grove is declared **before** the loop, and only
the insert goes **inside** the loop. This is the BED example with the record as the payload:

```cpp
#include <genogrove/io/bed_reader.hpp>
#include <genogrove/structure/grove/grove.hpp>
#include <genogrove/data_type/genomic_coordinate.hpp>
#include <fstream>
#include <iostream>

namespace gio = genogrove::io;
namespace gdt = genogrove::data_type;
namespace gst = genogrove::structure;

int main() {
    // genomic_coordinate keys, as in Python's BedGrove, so both write the same kind of file
    gst::grove<gdt::genomic_coordinate, gio::bed_entry> records(100);   // before the loop

    try {
        gio::bed_reader reader("genes.bed.gz");
        for (const auto& entry : reader) {
            // inside the loop: one insert for each record
            // the strand column is optional in BED: '.' when absent
            gdt::genomic_coordinate key{entry.strand.value_or('.'), entry.start, entry.end - 1};
            records.insert_data(entry.chrom, key, entry);
        }
    } catch (const std::runtime_error& e) {
        std::cerr << "Error: " << e.what() << "\n";
    }

    std::cout << "Loaded " << records.indexed_vertex_count() << " records\n";

    // Save to a .gg file and load it back (binary streams, see the serialization guide)
    {
        std::ofstream out("records.gg", std::ios::binary);
        records.serialize(out);
    }
    std::ifstream in("records.gg", std::ios::binary);
    auto reloaded = gst::grove<gdt::genomic_coordinate, gio::bed_entry>::deserialize(in);
    std::cout << "Reloaded " << reloaded.indexed_vertex_count() << " records\n";
    return 0;
}
```

Because this grove uses the same key type as `BedGrove`, Python can load the file with
`BedGrove.deserialize`. In C++ the key is always the coordinate you pass to `insert_data`, so
choosing the key yourself, as the last Python example does, is already covered by the loop above. The notes on `BedGrove` and
`GffGrove` in the Python tab (live records, unlabelled edges) describe those Python classes only.

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

The same example in Python reads `genes.bed.gz` and stores each record; `insert(index, entry)`
derives the key:

```python
import pygenogrove as pg

g = pg.BedGrove(100)

try:
    for e in pg.BedReader("genes.bed.gz"):
        g.insert(e.chrom, e)
except (RuntimeError, ValueError) as err:
    print("Error:", err)

print(f"Loaded {g.indexed_vertex_count()} records")

g.serialize("records.gg")
reloaded = pg.BedGrove.deserialize("records.gg")   # the BedEntry records are preserved
print(f"Reloaded {reloaded.indexed_vertex_count()} records")
```

Continuing from the grove `g` above, you can also build the record yourself and choose the key. The key's strand is up to you here; use
the record's strand so that strand-aware queries behave:

```python
entry = pg.BedEntry("chr1", 1000, 2000)       # BED coordinates: 0-based, half-open
entry.name = "BRCA1"
entry.strand = "+"
key = g.insert("chr1", pg.GenomicCoordinate("+", 1000, 1999), entry)

print(key.value.start, key.data.name)         # 1000 BRCA1
```

For a `GffEntry` the coordinates are 1-based, so the key is `[start - 1, end - 1]`. The fields of both
record types are listed in {doc}`/guide/io/bed` and {doc}`/guide/io/gff`.

::::

:::::
