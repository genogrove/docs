# Reading Genomic Files

genogrove reads the common genomic text and binary formats through a family of **readers**. Every
reader opens one file, yields one parsed record at a time, and is used the same way: construct it
with a path (and optional options), then iterate. Plain and gzip/BGZF-compressed inputs are detected
automatically.

| Format | Records | Native coordinates | Page |
|---|---|---|---|
| BED (BED3–BED12, bedGraph) | `bed_entry` / `BedEntry` | 0-based half-open `[start, end)` | {doc}`bed` |
| GFF3 / GTF | `gff_entry` / `GffEntry` | 1-based closed `[start, end]` | {doc}`gff` |
| SAM / BAM / CRAM | `sam_entry` / `SamEntry` | 0-based half-open `[start, end)` | {doc}`bam` |
| FASTA / FASTQ | `fasta_entry` / `FastaEntry` (streaming) and `fasta_index` / `FastaIndex` (random access) | 0-based half-open fetch | {doc}`fasta` |
| VCF / BCF | `vcf_entry` / `VcfEntry` | 0-based half-open `[start, end)` | {doc}`vcf` |

Three readers (BED, GFF, VCF) can also seek to one locus of an indexed file instead of streaming
the whole thing — see {doc}`region_access`. Loading records into a grove is covered in
{doc}`/guide/grove/loading_data`.

## The reader pattern

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

All readers live in `genogrove::io` and share one shape: construct, then range-for. Each is a
`file_reader<EntryType>` whose `begin()` is a **single-pass input iterator**.

```cpp
#include <genogrove/io/bed_reader.hpp>

namespace gio = genogrove::io;

gio::bed_reader reader("data.bed.gz");          // .gz handled automatically
for (const auto& entry : reader) {
    // entry is a const bed_entry&
}
```

Readers own htslib handles, so they are **non-copyable but movable**: pass them by reference or
`std::move` them. Call `begin()` at most once per reader — it consumes the first record eagerly so
`*it` is valid, and a second call on a non-empty file would skip a record.

::::

::::{tab-item} {{ py_tab }}
:sync: py

All readers share one shape: construct, then iterate with `for`.

```python
import pygenogrove as pg

for entry in pg.BedReader("data.bed.gz"):      # .gz handled automatically
    ...                                         # entry is a BedEntry
```

Readers are **single-pass**: each owns an htslib handle and cannot be restarted or iterated twice —
construct a new one to read again. They are not thread-safe; a call from another thread while
`__next__` is running raises `RuntimeError` (see {doc}`/guide/thread_safety`).

::::

:::::

## Coordinates: converting to grove keys

Readers keep each format's **native** convention. Grove keys are **0-based closed** `[start, end]`,
so convert when inserting:

| Format | Native | Grove key |
|---|---|---|
| BED / BAM / VCF | 0-based half-open `[start, end)` | `[start, end - 1]` |
| GFF / GTF | 1-based closed `[start, end]` | `[start - 1, end - 1]` |

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

```cpp
// BED / BAM / VCF: subtract 1 from end
grove.insert_data(entry.chrom, gdt::interval(entry.start, entry.end - 1), data);

// GFF / GTF: subtract 1 from both
grove.insert_data(entry.seqid, gdt::interval(entry.start - 1, entry.end - 1), data);
```

::::

::::{tab-item} {{ py_tab }}
:sync: py

The typed `BedGrove` / `GffGrove` do the conversion for you: `insert(index, entry)` derives the
key from the record's native coordinates. `SamEntry` and `VcfEntry` provide `to_coordinate()`.

```python
bed = pg.BedGrove(100)
for e in pg.BedReader("peaks.bed"):
    bed.insert(e.chrom, e)                              # key derived from the record

g = pg.Grove(100)
for aln in pg.BamReader("reads.bam"):
    g.insert(aln.chrom, aln.to_coordinate(), aln.to_dict())
```

Converting by hand: `pg.GenomicCoordinate(strand, e.start, e.end - 1)` for BED/BAM/VCF and
`pg.GenomicCoordinate(strand, e.start - 1, e.end - 1)` for GFF.

::::

:::::

## Compression and file types

The readers open **plain** and **gzip / BGZF** (`.gz`) files; nothing else is decompressed. Both
`bgzip` output and plain `gzip` output work under the `.gz` extension (htslib's `bgzf_open` reads
both), so files distributed as plain gzip — ENCODE GTFs, GENCODE annotations — need no
recompression. Only BGZF supports the random-access seeks that {doc}`region_access` needs.

A separate detector recognises a file's format and compression from its extension and magic bytes.
It also *recognises* BZIP2, XZ, ZSTD and LZ4, but the readers cannot open those — decompress first.

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

```cpp
#include <genogrove/io/filetype_detector.hpp>

auto [type, compression] = gio::filetype_detector::detect_filetype("data.bed.gz");
// type        == gio::filetype::BED
// compression == gio::compression_type::GZIP
```

`detect_filetype` is `static`; no detector object is needed. `filetype` covers BED, BEDGRAPH, GFF,
GTF, SAM, BAM, FASTA, FASTQ, VCF, GG and UNKNOWN; `compression_type` covers NONE, GZIP, BZIP2, XZ,
ZSTD, LZ4 and UNKNOWN.

::::

::::{tab-item} {{ py_tab }}
:sync: py

```python
ftype, comp = pg.FiletypeDetector.detect_filetype("data.bed.gz")
# (Filetype.BED, CompressionType.GZIP)
```

`detect_filetype` is a `staticmethod`. `Filetype` covers `BED`, `BEDGRAPH`, `GFF`, `GTF`, `SAM`,
`BAM`, `FASTA`, `FASTQ`, `VCF`, `GG` and `UNKNOWN`; `CompressionType` covers `NONE`, `GZIP`,
`BZIP2`, `XZ`, `ZSTD`, `LZ4` and `UNKNOWN`.

::::

:::::

## Errors and malformed records

By default a reader fails loudly: an unopenable file fails at construction, and a malformed record
fails during iteration with a message that names the line. The BED and GFF readers can instead
**skip** malformed records; `get_error_message()` then tells you what was skipped.

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

Readers throw `std::runtime_error`. Wrap iteration in `try` / `catch`:

```cpp
gio::bed_reader reader("data.bed");
try {
    for (const auto& entry : reader) { /* ... */ }
} catch (const std::runtime_error& e) {
    std::cerr << e.what() << "\n";            // e.g. "Invalid coordinate format at line 42"
}
```

Lenient mode for BED / GFF (`bam_reader` and `fasta_reader` have none; they throw only on I/O
errors):

```cpp
gio::bed_reader reader("data.bed", gio::bed_reader_options{.skip_invalid_lines = true});
for (const auto& entry : reader) {
    if (!reader.get_error_message().empty()) {
        std::cerr << "skipped: " << reader.get_error_message() << "\n";
    }
}
```

With `skip_invalid_lines` the first data record is treated like any other: a malformed first line is
skipped rather than failing construction. `get_error_message()` reflects the **most recently
attempted record** only — it is cleared at the start of every read, so after the loop ends it is
empty. A mid-stream BGZF/tabix I/O error both throws and records its message, so the message is
available in the `catch`.

::::

::::{tab-item} {{ py_tab }}
:sync: py

Readers raise `RuntimeError` — at construction for an unopenable file, during iteration for a
malformed record:

```python
try:
    for entry in pg.BedReader("data.bed"):
        ...
except RuntimeError as e:
    print(e)                                  # e.g. "Invalid coordinate format at line 42"
```

Lenient mode for `BedReader` / `GffReader` (`BamReader` and `FastaReader` have none):

```python
r = pg.BedReader("data.bed", skip_invalid_lines=True)
for entry in r:
    if r.get_error_message():
        print("skipped:", r.get_error_message())
```

With `skip_invalid_lines=True` a malformed first record is skipped rather than raising at
construction. `get_error_message()` reflects the most recently attempted record only and is empty
once iteration has finished; `get_current_line()` gives the 1-based line of the last record.

::::

:::::

## Files with no records

A structurally valid file that contains no records — empty, only blank lines, or only `#` comments
and headers — is **not** an error: the reader constructs normally and the loop body runs zero times.
Deciding what "no data" means is left to the caller.

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

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
entries = list(pg.GffReader(path))
if not entries:
    ...   # no records — warn, skip or fail as you see fit
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