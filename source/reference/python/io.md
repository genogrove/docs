# File readers and I/O

`pygenogrove` ships single-pass iterators for the common genomic file formats,
plus random-access FASTA and a format detector. Plain and gzip/BGZF-compressed
(`.gz`) inputs are auto-detected.

:::{note}
The readers are **single-pass** — each owns an htslib file handle and cannot be
restarted or iterated twice.
:::

## BedReader / GffReader

`BedReader` and `GffReader` iterate BED and GFF3/GTF files, yielding `BedEntry` /
`GffEntry` records (see {doc}`typed_groves`).

```python
import pygenogrove as pg

for entry in pg.BedReader("peaks.bed"):
    print(entry.chrom, entry.start, entry.end, entry.name)

# The common workflow: load a file into a typed grove. The 2-argument insert
# derives the grove's 0-based closed GenomicCoordinate key from each entry's
# native coordinates, so you don't hand-convert.
g = pg.BedGrove(256)
for e in pg.BedReader("peaks.bed"):
    g.insert(e.chrom, e)

gff = pg.GffGrove(256)
for e in pg.GffReader("genes.gff3"):
    gff.insert(e.seqid, e)

# bulk-load one chromosome at a time (insert_bulk is per-index):
g2 = pg.BedGrove(256)
g2.insert_bulk("chr1", [e for e in pg.BedReader("peaks.bed") if e.chrom == "chr1"])
```

```python
BedReader(path: str, skip_invalid_lines: bool = False)
GffReader(path: str, skip_invalid_lines: bool = False, validate_gtf: bool = False)
```

- A missing/unreadable `path` raises on construction.
- With `skip_invalid_lines=False` (default) a malformed line raises `RuntimeError`
  mid-iteration; with `True` such lines are skipped. The **first** data record is
  validated when the reader is constructed, so a malformed first record raises
  immediately regardless of this flag.
- `GffReader(..., validate_gtf=True)` enforces the mandatory GTF2 attributes
  (`gene_id`, `transcript_id`).
- Both expose `get_error_message()` and `get_current_line()` for diagnostics.

## BamReader (SAM/BAM alignments)

`BamReader` iterates SAM/BAM files (htslib auto-detects the format) yielding
`SamEntry` records, with filtering applied during iteration.

```python
import pygenogrove as pg

for aln in pg.BamReader("reads.bam", min_mapq=30):
    print(aln.qname, aln.chrom, aln.start, aln.end, aln.get_strand())

# load alignments into the universal Grove (sam_entry isn't serializable, so
# there is no typed BamGrove — route through to_coordinate() + to_dict())
g = pg.Grove(256)
for aln in pg.BamReader("reads.bam"):
    if aln.is_mapped():
        g.insert(aln.chrom, aln.to_coordinate(), aln.to_dict())
```

```python
BamReader(path, skip_unmapped=True, skip_secondary=False,
          skip_supplementary=False, skip_qc_fail=False,
          skip_duplicates=False, min_mapq=0)
```

- **`SamEntry`** fields: `qname`, `chrom`, `start`, `end` (0-based half-open),
  `mapq`, `sequence`, `quality`, `cigar` (string form), `flags` (an
  `AlignmentFlags`). Helpers: `get_strand()`, `is_primary()` / `is_mapped()` /
  `is_reverse()` / `is_secondary()` / `is_supplementary()` / `is_duplicate()` /
  `is_paired()` / …, `consumes_reference()`, `has_flag(flag)`.
- **`SamEntry.to_coordinate()`** derives the strand-aware `GenomicCoordinate` key
  (strand from FLAG; half-open `[start, end)` → closed `[start, end-1]`; raises for
  unmapped reads).
- **`SamEntry.to_dict()`** is a convenient JSON payload of the core fields.
- **`SamFlags`** exposes the standard FLAG bit constants; **`AlignmentFlags`** (the
  `.flags` object) has `value()` plus the same `is_*()` predicates.

:::{note}
CIGAR element detail (the op/length list), paired-end mate info, auxiliary tags,
and CRAM are not yet exposed.
:::

## FastaReader (FASTA/FASTQ sequences)

`FastaReader` iterates FASTA/FASTQ files yielding `FastaEntry` records. Sequences
are **named records, not intervals**, so this reader is standalone (no grove
integration).

```python
import pygenogrove as pg

for rec in pg.FastaReader("genome.fa"):
    print(rec.name, rec.comment, len(rec))

for rec in pg.FastaReader("reads.fq"):
    print(rec.name, rec.sequence, rec.quality)   # is_fastq() -> True
```

```python
FastaReader(path, skip_empty_sequences=False)
```

- **`FastaEntry`** fields: `name`, `comment`, `sequence`, `quality`
  (`Optional[str]` — set for FASTQ, `None` for FASTA); `is_fastq()`,
  `len(entry)` = sequence length. Constructible as `FastaEntry(name, sequence)`.

## FastaIndex (random-access FASTA)

`FastaIndex` provides random-access region fetches over a FASTA file, backed by an
`.fai` index (built on first open — the directory must be writable then). It pairs
with `FastaReader`: one streams, the other is random-access.

```python
import pygenogrove as pg

fa = pg.FastaIndex("genome.fa")
fa.fetch("chr1", 1000, 2000)   # bases of the 0-based half-open region [1000, 2000)
fa.fetch("chrM")               # the whole sequence
fa.sequence_length("chr1")     # length in bases
list(fa.names()), "chr1" in fa, len(fa)

# fetch a feature's bases: GenomicCoordinate is closed, fetch is half-open
gc = pg.GenomicCoordinate("+", 4, 7)
fa.fetch("chr1", gc.start, gc.end + 1)
```

- Methods: `fetch(name, start, end)` / `fetch(name)`, `sequence_count()`,
  `sequence_name(i)`, `sequence_length(name)`, `has_sequence(name)`, plus the
  Pythonic `len()` / `in` / `names()`.
- Unknown name / invalid region raise `IndexError`.

:::{important}
**Coordinate pairing:** `FastaIndex.fetch` is half-open `[start, end)` while a
`GenomicCoordinate` is closed `[start, end]`. Fetch a feature's bases with
`idx.fetch(name, gc.start, gc.end + 1)`, where `name` is the chromosome / grove
index (a `GenomicCoordinate` carries strand + start + end, not the chromosome).
:::

## FiletypeDetector (format detection)

`FiletypeDetector` infers a file's format and compression from its extension
(compression extension stripped first) and magic bytes.

```python
import pygenogrove as pg

ftype, comp = pg.FiletypeDetector().detect_filetype("peaks.bed.gz")
# (Filetype.BED, CompressionType.GZIP)
```

- `detect_filetype(path) -> (Filetype, CompressionType)`
- `Filetype`: `BED` / `BEDGRAPH` / `GFF` / `GTF` / `VCF` / `SAM` / `BAM` /
  `FASTA` / `FASTQ` / `GG` / `UNKNOWN`.
- `CompressionType`: `NONE` / `GZIP` / `BZIP2` / `XZ` / `ZSTD` / `LZ4` /
  `UNKNOWN`.