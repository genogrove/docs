# Reading Genomic Files

{term}`genogrove` reads the common genomic text and binary formats through a family of **readers**.
Every reader opens one file, yields one parsed record at a time, and is used the same way: construct
it with a path (and optional options), then iterate. Plain and gzip/BGZF-compressed inputs are
detected automatically. (BGZF, or "bgzip", is a gzip variant that allows seeking to a position inside
the compressed file.)

Before you start, install genogrove or {term}`pygenogrove` — {doc}`/guide/installation`
also shows how to compile and link the C++ examples. The file names in the snippets
(`data.bed.gz`, `peaks.bed`, `reads.bam`, …) stand for any file of that format; substitute your
own. Each format page below starts with a sample file of two or three lines that you can save and
use (the BAM page uses `samtools view` to make a small file from your own data).

| Format | Records | Native coordinates | Page |
|---|---|---|---|
| BED (BED3–BED12, bedGraph) | `bed_entry` / `BedEntry` | 0-based half-open `[start, end)` | {doc}`bed` |
| GFF3 / GTF | `gff_entry` / `GffEntry` | 1-based closed `[start, end]` | {doc}`gff` |
| SAM / BAM / CRAM | `sam_entry` / `SamEntry` | 0-based half-open `[start, end)` | {doc}`bam` |
| FASTA / FASTQ | `fasta_entry` / `FastaEntry` (streaming) and `fasta_index` / `FastaIndex` (random access) | 0-based half-open fetch | {doc}`fasta` |
| VCF / BCF | `vcf_entry` / `VcfEntry` | 0-based half-open `[start, end)` | {doc}`vcf` |

`[start, end)` means `start` is included and `end` is not: the record covers bases `start`
through `end - 1`. `[start, end]` includes both.

Three readers (BED, GFF, VCF) can also seek to one locus of an indexed file instead of streaming
the whole thing — see {doc}`region_access`. Loading records into a {term}`grove` is covered in
{doc}`/guide/grove/loading_data`.

## The reader pattern

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

All readers live in `genogrove::io` and share one shape: construct, then range-for. Each is a
`file_reader<EntryType>` (a {term}`template` filled in with the record type) whose `begin()` is a
**single-pass input {term}`iterator <iterator / iterable>`** — it can only move forward, once.

This fragment shows the shape; wrap it in `main()` to run it (every format page opens with a
complete program):

```cpp
#include <genogrove/io/bed_reader.hpp>

namespace gio = genogrove::io;                   // short alias for the namespace

gio::bed_reader reader("data.bed.gz");          // .gz handled automatically
for (const auto& entry : reader) {
    // entry is a const bed_entry&: read-only access to the current record
}
```

Readers own htslib handles (htslib is the samtools library genogrove reads files with), so you
cannot copy a reader. Pass it by reference, or hand it over with `std::move`. A range-`for` loop as
above needs nothing more. If you call `begin()` yourself, call it once per reader: it reads the first
record at once, and a second call on a non-empty file would skip a record.

::::

::::{tab-item} {{ py_tab }}
:sync: py

All readers share one shape: construct, then iterate with `for`.

```python
import pygenogrove as pg

for entry in pg.BedReader("data.bed.gz"):      # .gz handled automatically
    print(entry)                                # entry is a BedEntry
```

Readers are **single-pass**: each owns an htslib handle (htslib is the samtools library genogrove
reads files with) and cannot be restarted or iterated twice — construct a new one to read again.
They are not {term}`thread-safe`; a call from another thread while `__next__` (the method that `for` calls to get the next record) is running raises
`RuntimeError` (see {doc}`/guide/thread_safety`).

::::

:::::

## Coordinates: converting to grove keys

Readers keep each format's **native** convention. Grove {term}`keys <key>` are
**{term}`0-based closed`** `[start, end]`. Every record type converts itself: call `to_interval()`
for an unstranded key or `to_coordinate()` for a key that also carries the strand. The table shows
what the call does:

| Format | Native | Grove key |
|---|---|---|
| BED / BAM / VCF | 0-based half-open `[start, end)` | `[start, end - 1]` |
| GFF / GTF | 1-based closed `[start, end]` | `[start - 1, end - 1]` |

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

Fragments: `g` is a `gst::grove<gdt::interval, std::string>` (a grove with interval keys and string
payloads; see {doc}`/guide/grove/index`), `entry` the record from a reader loop and `data` the
{term}`payload` to store ({doc}`bed` has the complete program, with the alias lines below).

```cpp
namespace gdt = genogrove::data_type;            // alias for the key types
namespace gst = genogrove::structure;            // alias for the grove

// BED / BAM / VCF record: the call subtracts 1 from end
g.insert_data(entry.chrom, entry.to_interval(), data);

// GFF / GTF record: the call subtracts 1 from both start and end
g.insert_data(entry.seqid, entry.to_interval(), data);
```

`bed_entry`, `gff_entry`, `sam_entry` and `vcf_entry` all have two members:
`gdt::interval to_interval() const` and `gdt::genomic_coordinate to_coordinate() const`. The
coordinate form adds the strand: BED column 6, GFF column 7 (`?` and no strand become `.`), the SAM
FLAG, and `.` for VCF. An unset BED strand is `.`.

Two records have no closed form, so their conversion throws `std::invalid_argument`: a `bed_entry`
with `end <= start`, and a `sam_entry` that uses no reference bases (check `consumes_reference()`
first). The GFF and VCF conversions do not check. Parsed records always satisfy them, but a record
you build by hand with `start == 0` (GFF) or `end <= start` (VCF) wraps around to a huge number.

::::

::::{tab-item} {{ py_tab }}
:sync: py

Every record type has `to_coordinate()`, which returns the `GenomicCoordinate` key with the
strand. The typed `BedGrove` / `GffGrove` call it for you: `insert(index, entry)` derives the key
from the record's native coordinates.

```python
import pygenogrove as pg

bed = pg.BedGrove(100)                                  # 100 = tree order, a good default
for e in pg.BedReader("peaks.bed"):
    bed.insert(e.chrom, e)                              # key derived from the record

gff = pg.GffGrove(100)
for e in pg.GffReader("annotations.gtf.gz"):
    gff.insert(e.seqid, e)                              # 1-based closed -> 0-based closed

bed_g = pg.Grove(100)
for e in pg.BedReader("peaks.bed"):
    bed_g.insert(e.chrom, e.to_coordinate(), e.name or "unnamed")   # the key, built by hand

g = pg.Grove(100)
for aln in pg.BamReader("reads.bam"):
    if aln.consumes_reference():                        # skip zero-length alignments
        # to_coordinate(): half-open [start, end) -> 0-based closed [start, end - 1]
        g.insert(aln.chrom, aln.to_coordinate(), aln.qname)

vcf = pg.Grove(100)
for v in pg.VcfReader("calls.vcf.gz"):
    vcf.insert(v.chrom, v.to_coordinate(), v.id)        # same conversion: [start, end - 1]
```

The C++ fragment above stores a string as payload (`data`); the BAM and VCF lines store the read name and the ID
the same way, while the typed groves store the whole record. The key conversion is the same.

`BedEntry.to_coordinate()` raises `ValueError` if `end <= start`, and `GffEntry.to_coordinate()`
raises it if `start < 1` or `end < start`. `SamEntry.to_coordinate()` raises it for a read that
uses no reference bases (check `consumes_reference()` first), and `VcfEntry.to_coordinate()` raises
it if the record spans no reference bases. So the Python calls check where the C++ GFF and VCF calls
do not. `BedEntry.to_coordinate()` and `GffEntry.to_coordinate()` exist in pygenogrove 0.10.0 and
later.

::::

:::::

## Compression and file types

The readers open **plain** and **gzip / BGZF** (`.gz`) files; nothing else is decompressed. Both
`bgzip` output and plain `gzip` output work under the `.gz` extension (htslib reads both), so files distributed as plain gzip — ENCODE GTFs, GENCODE annotations — need no
recompression. Only BGZF supports the random-access seeks that {doc}`region_access` needs.

A separate detector recognises a file's format and compression from its extension and
{term}`magic bytes <magic>`. It also *recognises* BZIP2, XZ, ZSTD and LZ4, but the readers cannot
open those — decompress first.

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

```cpp
#include <genogrove/io/filetype_detector.hpp>

// the call returns two values at once; `auto [a, b]` names them
auto [type, compression] = gio::filetype_detector::detect_filetype("data.bed.gz");
// type        == gio::filetype::BED
// compression == gio::compression_type::GZIP
```

`detect_filetype` is `static` (called on the class, no detector object is needed). `filetype`
covers BED, BEDGRAPH, GFF, GTF, SAM, BAM, FASTA, FASTQ, VCF, GG and UNKNOWN; `compression_type`
covers NONE, GZIP, BZIP2, XZ, ZSTD, LZ4 and UNKNOWN.

::::

::::{tab-item} {{ py_tab }}
:sync: py

```python
import pygenogrove as pg

ftype, comp = pg.FiletypeDetector.detect_filetype("data.bed.gz")
print(ftype, comp)                              # Filetype.BED CompressionType.GZIP
```

`detect_filetype` is a `staticmethod` (called on the class, no detector object is needed).
`Filetype` covers `BED`, `BEDGRAPH`, `GFF`, `GTF`, `SAM`, `BAM`, `FASTA`, `FASTQ`, `VCF`, `GG` and
`UNKNOWN`; `CompressionType` covers `NONE`, `GZIP`, `BZIP2`, `XZ`, `ZSTD`, `LZ4` and `UNKNOWN`.

::::

:::::

## Errors and malformed records

By default a reader fails loudly: an unopenable file, or a malformed **first** record, fails at
construction; a malformed later record fails during iteration. Messages name the offending line.
The BED and GFF readers can instead **skip** malformed records.

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

Readers report failures as {term}`exceptions <exception>` of type `std::runtime_error`. Construct
and iterate inside one `try` so both construction and per-record failures are caught (fragments;
`gio` is the alias from above):

```cpp
try {
    gio::bed_reader reader("data.bed");
    for (const auto& entry : reader) { /* ... */ }
} catch (const std::runtime_error& e) {
    std::cerr << e.what() << "\n";            // e.what() is the message,
}                                             // e.g. "Invalid coordinate format at line 42"
```

Lenient mode for BED / GFF:

```cpp
gio::bed_reader reader("data.bed", gio::bed_reader_options{.skip_invalid_lines = true});
for (const auto& entry : reader) { /* only well-formed records arrive here */ }
```

`{.skip_invalid_lines = true}` sets one named field of the options and leaves the rest at their
defaults. With `skip_invalid_lines` a malformed first line is skipped like any other rather than
failing construction. Skipped records are **silent**: the reader clears its error message at the
start of every read attempt and keeps reading until a record parses, so by the time your loop body
runs the message is empty again. To find out what a file contains that would be skipped, read it
once without the flag. `get_error_message()` is useful after a *caught* exception — a mid-stream
BGZF/tabix I/O error records its message before propagating.

`bam_reader` and `fasta_reader` have no lenient mode; they throw on I/O errors and on truncated
records (auxiliary data — the optional tags at the end of a record — in BAM, quality strings in
FASTQ).

::::

::::{tab-item} {{ py_tab }}
:sync: py

Readers raise `RuntimeError` — at construction for an unopenable file, during iteration for a
malformed record:

```python
import pygenogrove as pg

try:
    for entry in pg.BedReader("data.bed"):
        print(entry)
except RuntimeError as e:
    print(e)                                  # e.g. "Invalid coordinate format at line 42"
```

Lenient mode for `BedReader` / `GffReader`:

```python
for entry in pg.BedReader("data.bed", skip_invalid_lines=True):
    print(entry)                              # only well-formed records arrive here
```

With `skip_invalid_lines=True` a malformed first record is skipped like any other rather than
raising at construction. Skipped records are **silent**: the reader clears its error message at the
start of every read attempt and keeps reading until a record parses, so `get_error_message()` is
empty by the time your loop body runs. To find out what would be skipped, read the file once without
the flag. `get_current_line()` gives the 1-based line of the last record.

`BamReader` and `FastaReader` have no lenient mode; they raise `RuntimeError` on I/O errors and on
truncated records (auxiliary data — the optional tags at the end of a record — in BAM, quality
strings in FASTQ).

::::

:::::

## Files with no records

For the BED and GFF readers, a structurally valid file that contains no records — empty, only
blank lines, or only `#` comments and headers — is **not** an error: the reader constructs
normally and the loop body runs zero times. Deciding what "no data" means is left to the caller.
VCF/BCF and BAM files must carry a header, so a zero-byte file fails at construction there; a
header-only file yields zero records.

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

Fragment; `path` is the file name:

```cpp
gio::gff_reader reader(path);
bool any = false;
for (const auto& entry : reader) { any = true; /* ... */ }
if (!any) { /* no records — warn, skip or fail as you see fit */ }
```

Or, without iterating, `reader.begin() == reader.end()` — but remember that `begin()` consumes a
record on a non-empty file, so do not call it again afterwards.

::::

::::{tab-item} {{ py_tab }}
:sync: py

```python
import pygenogrove as pg

entries = list(pg.GffReader(path))            # path is the file name
if not entries:
    print("no records")                       # warn, skip or fail as you see fit
```

::::

:::::

```{toctree}
:maxdepth: 1
:hidden:

bed
gff
bam
fasta
vcf
region_access
```
