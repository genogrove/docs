# Reading Genomic Files (I/O)

Genogrove provides efficient readers for common genomic file formats with automatic compression detection.

:::::{tab-set}

::::{tab-item} C++

The `genogrove::io` namespace provides efficient readers for common genomic file formats with automatic compression detection.

### Reader Ownership

All streaming file readers (`bed_reader`, `gff_reader`, `bam_reader`, `fasta_reader`) own raw
htslib resource pointers and are **non-copyable** but **movable**. Attempting to copy a reader will
produce a compile error. `fasta_index` (indexed random-access FASTA) follows the same rule.

```cpp
namespace gio = genogrove::io;

gio::bed_reader reader("data.bed");

// gio::bed_reader copy = reader;            // compile error — not copyable
gio::bed_reader moved = std::move(reader);   // OK — transfers ownership
```

When passing readers to functions, use a reference or move them:

```cpp
namespace gio = genogrove::io;

void process(gio::bed_reader& reader) {      // pass by reference
    for (const auto& entry : reader) { /* ... */ }
}
```

### Automatic File Type Detection

Genogrove can automatically detect file types and compression formats:

```cpp
#include <genogrove/io/filetype_detector.hpp>

namespace gio = genogrove::io;

int main() {
    gio::filetype_detector detector;
    auto [filetype, compression] = detector.detect_filetype("data.bed.gz");

    // filetype will be gio::filetype::BED
    // compression will be gio::compression_type::GZIP

    return 0;
}
```

**Supported File Types:**

- BED (Browser Extensible Data)
- BEDGRAPH
- GFF (General Feature Format)
- GTF (Gene Transfer Format)
- BAM/SAM/CRAM (Sequence Alignments)
- FASTA (`.fa`, `.fasta`, `.fna`)
- FASTQ (`.fq`, `.fastq`, `.fnq`)
- VCF (Variant Call Format)
- GG (Genogrove native format)

**Supported Compression Formats:**

- GZIP (.gz, including BGZF)
- BZIP2 (.bz2)
- XZ (.xz, LZMA)
- ZSTD (.zst)
- LZ4 (.lz4)

For `bed_reader` and `gff_reader`, both BGZF (block-gzip, `bgzip`) and plain gzip
(`gzip`) compressed inputs are accepted with the `.gz` extension — internally they
share htslib's `bgzf_open()`, which reads both formats transparently. BGZF files
support random-access seeks; plain gzip files are read sequentially. This is useful
when consuming files from sources that distribute plain-gzip compression (e.g.,
ENCODE GTFs, GENCODE annotations) — there is no need to re-compress with `bgzip`.

### Iterator Equality Contract

The iterator returned by `reader.begin()` is a **single-pass input iterator**. Equality is
position-aware:

- End iterators (`reader.end()`) compare equal to each other.
- A non-end iterator compares equal to an end iterator only if it has hit EOF or an error.
- Two non-end iterators are equal **iff they share the same parent reader AND have advanced
  the same number of times** (an internal monotonic position counter is bumped on each
  successful advance).

The common range-for pattern (`for (const auto& entry : reader)`) and the `it != reader.end()`
loop are unaffected by this rule. The rule matters only when you copy an iterator and advance
one copy — that pattern violates the single-pass nature of the underlying reader anyway (the
older copy keeps its cached `current_entry_` but the reader state has moved forward), so it is
not a recommended idiom; the equality contract just makes the resulting iterators distinguishable
rather than silently equal.

### Error Handling

All file readers throw `std::runtime_error` on parse and I/O errors by default. The `read_next()`
method returns `false` only at end-of-file. Wrap iteration in a try-catch to handle errors:

```cpp
namespace gio = genogrove::io;

gio::bed_reader reader("data.bed");

try {
    for (const auto& entry : reader) {
        // process entries...
    }
} catch (const std::runtime_error& e) {
    std::cerr << "Error: " << e.what() << "\n";
    // error messages include the line number, e.g.
    // "Invalid coordinate format at line 42"
}
```

This pattern applies to all readers (`bed_reader`, `gff_reader`, `bam_reader`).

#### Lenient Mode

To skip malformed records instead of throwing, enable lenient mode via the reader's options struct.
Use `get_error_message()` to check for errors on individual records:

```cpp
namespace gio = genogrove::io;

// BED: skip_invalid_lines
gio::bed_reader reader("data.bed", gio::bed_reader_options{.skip_invalid_lines = true});

// GFF: skip_invalid_lines
// gio::gff_reader reader("data.gff", gio::gff_reader_options{.skip_invalid_lines = true});

// BAM: bam_reader throws only on I/O errors — no lenient mode option

for (const auto& entry : reader) {
    // process entries — malformed lines are silently skipped
}
```

#### Error Message Lifecycle

`get_error_message()` reflects the **most recently attempted record** only — it is cleared at the
start of each iteration. It does not accumulate errors across records.

- **During iteration**: contains the error from the last skipped record (if any), or is empty if the
  last record was valid.
- **After iteration completes**: empty, because the final read was EOF (no error).

To log every skipped record, check `get_error_message()` inside the loop:

```cpp
for (const auto& entry : reader) {
    if (!reader.get_error_message().empty()) {
        std::cerr << "Skipped: " << reader.get_error_message() << "\n";
    }
    // process valid entry...
}
```

#### Zero-Record Inputs

For `bed_reader` and `gff_reader`, structurally valid inputs that contain no records — empty files,
files where every line is blank, and files that contain only `#`-prefixed comments or header lines —
are **not** an error. The constructor returns successfully and the iterator immediately compares
equal to `end()`, so the body of a `for (...)` loop simply runs zero times.

This means callers decide the policy for "no data" rather than the reader. Detect zero records
either by checking inside the loop or by comparing iterators directly:

```cpp
gio::gff_reader reader(path);

bool any = false;
for (const auto& entry : reader) {
    any = true;
    // process entry...
}
if (!any) {
    // no records — consumer-defined policy: warn, skip, or fail
}
```

The iterator is single-pass: each call to `begin()` on a reader that still has data
consumes the next record from the underlying stream (the iterator's constructor calls
`read_next()` eagerly so that `*it` is immediately valid). Call `begin()` at most once
per reader. When detecting empty inputs without iterating, do the comparison and stop:

```cpp
gio::gff_reader reader(path);
if (reader.begin() == reader.end()) {
    // no records — safe: begin() consumed nothing because the file was empty
}
// do not call begin() again on the same reader if you already called it above —
// for a non-empty file, that second call would skip the first record
```

The following error conditions still throw `std::runtime_error` (or skip the line, in lenient mode):

- File-open failures (missing file, permission denied, unreadable BGZF header)
- Malformed first record that fails to parse
- Per-line parse errors discovered mid-iteration

In other words, "valid file with zero records" is now a quiet success; only structurally broken
inputs raise errors.

### Coordinate Semantics

Readers preserve format-native coordinate conventions. The grove uses **closed** `[start, end]` coordinates (both endpoints inclusive). When inserting reader entries, convert as needed:

| Format    | Convention             | Conversion to grove interval                        |
|-----------|------------------------|-----------------------------------------------------|
| BED / BAM | 0-based half-open `[start, end)` | `gdt::interval(entry.start, entry.end - 1)` |
| GFF / GTF | 1-based inclusive `[start, end]` | `gdt::interval(entry.start, entry.end)`      |

```cpp
// BED / BAM — subtract 1 from end
for (const auto& entry : bed_reader) {
    grove.insert_data(entry.chrom,
                      gdt::interval(entry.start, entry.end - 1),
                      data);
}

// GFF / GTF — use start and end directly (both already inclusive)
for (const auto& entry : gff_reader) {
    grove.insert_data(entry.seqid,
                      gdt::interval(entry.start, entry.end),
                      data);
}
```

### BED Files

BED files store genomic intervals with optional metadata. The `bed_reader` provides iterator-based access:

```cpp
#include <genogrove/io/bed_reader.hpp>
#include <iostream>

namespace gio = genogrove::io;

int main() {
    // Automatically handles compressed files (.bed.gz)
    gio::bed_reader reader("example.bed");

    try {
        for (const auto& entry : reader) {
            std::cout << "Chromosome: " << entry.chrom << "\n"
                      << "Start: " << entry.start << "\n"
                      << "End: " << entry.end << "\n";

            // Optional fields (if present in file)
            if (entry.name) {
                std::cout << "Name: " << *entry.name << "\n";
            }
            if (entry.strand) {
                std::cout << "Strand: " << *entry.strand << "\n";
            }
        }
    } catch (const std::runtime_error& e) {
        std::cerr << "Parse error: " << e.what() << "\n";
    }

    return 0;
}
```

#### Mixed BED Formats

The `bed_reader` supports files that mix BED3, BED6, and BED12 records. Optional fields are reset
on each record, so a BED6 line following a BED12 line will not carry over stale block or RGB data:

```cpp
gio::bed_reader reader("mixed.bed");

for (const auto& entry : reader) {
    // Always present (BED3)
    std::cout << entry.chrom << "\t"
              << entry.start << "\t"
              << entry.end;

    // Only set on BED6+ lines
    if (entry.name)   std::cout << "\t" << *entry.name;
    if (entry.score)  std::cout << "\t" << *entry.score;
    if (entry.strand) std::cout << "\t" << *entry.strand;

    // Only set on BED12 lines
    if (entry.blocks)  std::cout << "\t(has blocks)";

    std::cout << "\n";
}
```

#### BED Entry Fields

- `chrom` (std::string): Chromosome name
- `start` (size_t): Start position (0-based, half-open)
- `end` (size_t): End position (0-based, half-open)
- `name` (std::optional\<std::string>): Feature name
- `score` (std::optional\<int>): Score value
- `strand` (std::optional\<char>): Strand (+/-)
- `thickness` (std::optional\<thick_info>): Display thickness coordinates
- `item_rgb` (std::optional\<rgb_color>): RGB color value
- `blocks` (std::optional\<block_info>): Block information

### GFF/GTF Files

GFF3 and GTF files contain gene annotations. The `gff_reader` auto-detects the format variant
by inspecting the attribute column (GFF3 uses `key=value`, GTF uses `key "value"`).
Coordinates are stored in native GFF format: **1-based inclusive** `[start, end]`.

```cpp
#include <genogrove/io/gff_reader.hpp>
#include <iostream>

namespace gio = genogrove::io;

int main() {
    gio::gff_reader reader("annotations.gff");

    try {
        for (const auto& entry : reader) {
            std::cout << "Sequence: " << entry.seqid << "\n"
                      << "Type: " << entry.type << "\n"
                      << "Start: " << entry.start << "\n"
                      << "End: " << entry.end << "\n";

            // Access attributes (column 9)
            if (auto gene_id = entry.get_gene_id()) {
                std::cout << "Gene ID: " << *gene_id << "\n";
            }

            // Check format
            if (entry.is_gtf()) {
                std::cout << "Format: GTF\n";
            } else if (entry.is_gff3()) {
                std::cout << "Format: GFF3\n";
            }
        }
    } catch (const std::runtime_error& e) {
        std::cerr << "Parse error: " << e.what() << "\n";
    }

    return 0;
}
```

#### GFF Entry Fields

- `seqid` (std::string): Chromosome/contig name
- `source` (std::string): Source of the feature
- `type` (std::string): Feature type (gene, exon, CDS, etc.)
- `start` (size_t): Start position (1-based inclusive, native GFF format)
- `end` (size_t): End position (1-based inclusive, native GFF format)
- `score` (std::optional\<double>): Score value (`std::nullopt` when `.` in file)
- `strand` (std::optional\<char>): Strand (+, -, ., or ?)
- `phase` (std::optional\<int>): Phase for CDS features (0, 1, or 2)
- `attributes` (std::map\<std::string, std::string, std::less\<>>): Key-value pairs from column 9 (transparent comparator enables `string_view` lookups)
- `format` (gff_format): Detected format — `gff_format::GFF3`, `gff_format::GTF`, or `gff_format::UNKNOWN`

#### Attribute Access

Helper methods return `std::optional<std::string>` (or `std::optional<int>` for `get_exon_number()`).
Some helpers try multiple attribute keys to work across GFF3 and GTF conventions:

- `get_gene_id()` — returns `gene_id`
- `get_transcript_id()` — returns `transcript_id`
- `get_exon_number()` — parses `exon_number` as `int`
- `get_gene_name()` — tries `gene_name`, then falls back to GFF3's `Name`
- `get_gene_biotype()` — tries `gene_biotype`, `gene_type`, then `biotype`
- `get_attribute(key)` — generic getter for any attribute key (accepts `std::string_view`)

You can also access the attributes map directly:

```cpp
// Direct map access
auto it = entry.attributes.find("ID");
if (it != entry.attributes.end()) {
    std::cout << "ID: " << it->second << "\n";
}
```

#### GTF Quoted Semicolons

Semicolons inside double-quoted GTF attribute values (e.g., `gene_name "test;name"`) are correctly
preserved. The parser recognizes that these are part of the value rather than field delimiters.
GFF3 files are unaffected — GFF3 uses URL-encoding (`%3B`) for literal semicolons per spec.

#### GTF Validation

GTF attribute validation is **opt-in** via the `validate_gtf` option (default: `false`). When
enabled on GTF-format files, the reader enforces mandatory GTF2 attributes:

- `gene_id` is required on **all** features
- `transcript_id` is required on exon, CDS, start_codon, stop_codon, UTR, 5UTR, and 3UTR features

If validation fails, `read_next()` throws `std::runtime_error` (or skips the line when
`skip_invalid_lines` is enabled). GFF3 files are unaffected regardless of this setting.

```cpp
// Enable GTF validation
gio::gff_reader reader("annotations.gtf",
    gio::gff_reader_options{.validate_gtf = true});

// Combine with lenient mode to skip invalid records instead of throwing
gio::gff_reader lenient_reader("annotations.gtf",
    gio::gff_reader_options{.skip_invalid_lines = true, .validate_gtf = true});
```

#### Convenience Methods

- `is_gtf()` — returns `true` if format is GTF
- `is_gff3()` — returns `true` if format is GFF3

### BAM/SAM Files

BAM, SAM, and CRAM files store sequence alignments. The `bam_reader` auto-detects the format and handles
decompression via htslib. SAM uses 1-based positions (POS); these are converted to 0-based half-open
`[start, end)` values using the CIGAR string to compute the aligned reference length.

```{note}
**`read_next()` error contract.** When `read_next()` returns `true` the record is fully populated
and `get_error_message()` reads empty. `bam_reader::read_next()` throws `std::runtime_error` on
both I/O errors **and on truncated auxiliary data** (`"Truncated auxiliary data at record N"`) —
truncated aux is no longer a silent post-hoc warning in `get_error_message()`. Always wrap BAM
iteration in `try`/`catch` rather than relying on a post-loop `get_error_message()` check to
detect aux truncation.
```

```cpp
#include <genogrove/io/bam_reader.hpp>
#include <iostream>

namespace gio = genogrove::io;

int main() {
    gio::bam_reader reader("alignments.bam");

    try {
        for (const auto& entry : reader) {
            std::cout << "Read: " << entry.qname << "\n"
                      << "Chrom: " << entry.chrom << "\n"
                      << "Start: " << entry.start << "\n"
                      << "End: " << entry.end << "\n"
                      << "Strand: " << entry.get_strand() << "\n"
                      << "MAPQ: " << static_cast<int>(entry.mapq) << "\n"
                      << "CIGAR: " << entry.cigar_string_repr() << "\n";

            if (entry.mate) {
                std::cout << "Mate chrom: " << entry.mate->chrom << "\n"
                          << "Mate pos: " << entry.mate->position << "\n"
                          << "Insert size: " << entry.mate->insert_size << "\n";
            }
        }
    } catch (const std::runtime_error& e) {
        std::cerr << "Read error: " << e.what() << "\n";
    }

    return 0;
}
```

#### Filtering Options

Use factory methods on `bam_reader_options` to apply common filters, or build a custom options struct:

```cpp
namespace gio = genogrove::io;

// Factory presets
gio::bam_reader reader1("reads.bam", gio::bam_reader_options::defaults());       // skip unmapped (default)
gio::bam_reader reader2("reads.bam", gio::bam_reader_options::include_all());    // no filtering
gio::bam_reader reader3("reads.bam", gio::bam_reader_options::primary_only());   // primary alignments only
gio::bam_reader reader4("reads.bam", gio::bam_reader_options::high_quality(20)); // MAPQ >= 20

// Custom options
gio::bam_reader_options opts;
opts.skip_unmapped = true;
opts.skip_secondary = true;
opts.skip_duplicates = true;
opts.min_mapq = 30;
gio::bam_reader reader5("reads.bam", opts);
```

**Filter fields:**

- `skip_unmapped` (bool, default `true`): Skip unmapped reads
- `skip_secondary` (bool, default `false`): Skip secondary alignments
- `skip_supplementary` (bool, default `false`): Skip supplementary alignments
- `skip_qc_fail` (bool, default `false`): Skip QC-failed reads
- `skip_duplicates` (bool, default `false`): Skip duplicate reads
- `min_mapq` (uint8_t, default `0`): Minimum mapping quality

#### SAM Entry Fields

- `qname` (std::string): Read name
- `chrom` (std::string): Reference sequence name
- `start` (size_t): Start position (0-based, half-open, computed from POS). For unmapped reads and for records whose CIGAR consumes zero reference bases (pure soft-clip `100S`, hard-clip-only secondary alignments `100H`+`FLAG=256`), `start == POS` and `end == start` — gate on `consumes_reference()` before treating the record as a real interval.
- `end` (size_t): End position (0-based, half-open, computed from POS + CIGAR-consumed reference length). Equals `start` for unmapped / zero-ref-consuming records (see above).
- `flags` (alignment_flags): Bitwise flags with convenience methods (`is_paired()`, `is_reverse()`, `is_duplicate()`, etc.)
- `mapq` (uint8_t): Mapping quality
- `cigar` (cigar_string): CIGAR operations as a `std::vector<cigar_element>`
- `sequence` (std::string): Read sequence
- `quality` (std::string): ASCII quality scores
- `mate` (std::optional\<mate_info>): Mate information (`chrom`, `position`, `insert_size`)
- `tags` (sam_tags): Auxiliary tags (`std::unordered_map<std::string, sam_tag_value>`)

#### CIGAR Operations

Each `cigar_element` has an `op` (operation code) and a `length`. Reference-consuming operations
(M, D, N, =, X) determine the aligned interval length.

```cpp
for (const auto& elem : entry.cigar) {
    std::cout << elem.length << elem.to_char();        // e.g. "50M2I30M"
    if (elem.consumes_reference()) { /* M, D, N, =, X */ }
    if (elem.consumes_query())     { /* M, I, S, =, X */ }
}
```

#### Tag Access

Auxiliary tags are stored in an `std::unordered_map<std::string, sam_tag_value>`. The value is a
`std::variant` supporting `char`, `int64_t`, `float`, `std::string`, and typed vectors.

```cpp
auto it = entry.tags.find("NH");
if (it != entry.tags.end()) {
    int64_t num_hits = std::get<int64_t>(it->second);
    std::cout << "Number of hits: " << num_hits << "\n";
}
```

#### Header Access

The `bam_reader` provides methods to inspect the SAM header and reference sequences before or after iteration:

- `get_header()` — returns the full SAM header text (all `@HD`, `@SQ`, `@RG`, `@PG` lines)
- `get_reference_names()` — returns a `std::vector<std::string>` of reference sequence names from the header

```cpp
namespace gio = genogrove::io;

gio::bam_reader reader("alignments.bam");

// Inspect reference sequences
const auto& refs = reader.get_reference_names();
std::cout << "References (" << refs.size() << "):\n";
for (const auto& name : refs) {
    std::cout << "  " << name << "\n";
}

// Access the raw SAM header (e.g., to find read groups)
const std::string& header = reader.get_header();
std::cout << "Header:\n" << header << "\n";
```

#### Convenience Methods

- `get_strand()` — returns `'+'`, `'-'`, or `'.'`
- `is_primary()` — not secondary and not supplementary
- `is_mapped()` — not unmapped
- `consumes_reference()` — `true` iff the record covers any reference bases (`start < end`). Returns `false` for unmapped reads and for mapped records whose CIGAR consumes zero reference bases (pure soft-clip, hard-clip-only secondary alignments). Use this as the gate before converting to a closed `gdt::interval(start, end - 1)` or inserting into a grove — the closed-interval conversion underflows otherwise.
- `cigar_string_repr()` — CIGAR as a human-readable string (e.g. `"50M2I30M"`)

```cpp
// Recommended insertion pattern: gate on consumes_reference()
for (const auto& entry : reader) {
    if (!entry.consumes_reference()) continue;   // skip soft-clip / hard-clip-only
    grove.insert_data(entry.chrom,
                      gdt::interval(entry.start, entry.end - 1),
                      entry);
}
```

### FASTA / FASTQ Files

Genogrove provides two complementary APIs for FASTA/FASTQ data:

- **`fasta_reader`** — streaming iteration over every record in a FASTA or FASTQ file
  (including gzip-compressed variants). Follows the same `file_reader<EntryType>` iterator pattern
  as the other readers. Backed by htslib's `kseq` parser.
- **`fasta_index`** — indexed random-access reader for `.fa` / `.fasta` / `.fna` files. Fetches
  regions or whole sequences in O(1) using a `.fai` index (auto-created on first use). Backed by
  htslib's `faidx` API.

#### Streaming: `fasta_reader`

```cpp
#include <genogrove/io/fasta_reader.hpp>
#include <iostream>

namespace gio = genogrove::io;

int main() {
    gio::fasta_reader reader("reads.fq.gz");

    try {
        for (const auto& entry : reader) {
            std::cout << entry.name << " (" << entry.sequence.size() << " bp)\n";
            if (entry.quality) {
                std::cout << "  quality: " << *entry.quality << "\n";
            }
        }
    } catch (const std::runtime_error& e) {
        std::cerr << "Parse error: " << e.what() << "\n";
    }
    return 0;
}
```

- Format (FASTA vs. FASTQ) is auto-detected per record by `kseq` — mixed `>` and `@` headers are
  handled transparently.
- `entry.quality` is `std::optional<std::string>` — populated for FASTQ records, `std::nullopt`
  for FASTA records.
- `fasta_reader_options{.skip_empty_sequences = true}` skips records whose sequence is empty.
- `fasta_reader` has no lenient mode: `read_next()` throws `std::runtime_error` on truncated
  quality strings or I/O errors, so use the same try/catch pattern shown for `bam_reader` above.

#### FASTA Entry Fields

- `name` (std::string): Sequence name (text after `>` or `@`, up to the first whitespace)
- `comment` (std::string): Rest of the header line after the name (empty if none)
- `sequence` (std::string): Nucleotide sequence
- `quality` (std::optional\<std::string>): Per-base quality string (FASTQ only, `std::nullopt` for FASTA)

#### Indexed Access: `fasta_index`

`fasta_index` is useful when you already have genomic coordinates (e.g., from a BED or GFF file)
and want to pull out the underlying sequence without scanning the entire FASTA.

```cpp
#include <genogrove/io/fasta_index.hpp>
#include <iostream>

namespace gio = genogrove::io;

int main() {
    // Opens the FASTA and loads (or creates) its .fai index.
    gio::fasta_index fasta("genome.fa");

    // Fetch a region — coordinates are 0-based half-open [start, end),
    // matching BED / BAM conventions.
    std::string promoter = fasta.fetch("chr1", 1000, 2000);

    // Fetch an entire sequence by name.
    std::string chrM = fasta.fetch("chrM");

    // Enumerate sequences in the index.
    for (size_t i = 0; i < fasta.sequence_count(); ++i) {
        auto name = fasta.sequence_name(i);
        std::cout << name << ": " << fasta.sequence_length(name) << " bp\n";
    }

    if (fasta.has_sequence("chrUn")) {
        // ...
    }
}
```

**Coordinate reminder**: `fetch(name, start, end)` follows BED/BAM's 0-based half-open convention.
When pairing with a GFF/GTF record (which is 1-based inclusive), shift the start by one:

```cpp
// GFF: 1-based inclusive [start, end] → FASTA: 0-based half-open [start-1, end)
for (const auto& entry : gff_reader) {
    std::string seq = fasta.fetch(entry.seqid, entry.start - 1, entry.end);
    // ...
}
```

**Notes:**

- All `fasta_index` lookup methods (`fetch`, `sequence_name`, `sequence_length`) throw
  `std::out_of_range` on unknown sequence names or out-of-range indices; `fetch` additionally
  throws `std::out_of_range` on invalid regions (`start >= end`, or a region exceeding htslib's
  coordinate limit). `std::runtime_error` is reserved for an actual htslib fetch failure.
- The `.fai` file is created on first use if missing (requires write permission to the FASTA
  directory).
- `fasta_index` is non-copyable and movable.

::::

::::{tab-item} Python

`pygenogrove` ships single-pass iterators for the common genomic file formats,
plus random-access FASTA and a format detector. Plain and gzip/BGZF-compressed
(`.gz`) inputs are auto-detected.

:::{note}
The readers are **single-pass** — each owns an htslib file handle and cannot be
restarted or iterated twice.
:::

### BedReader / GffReader

`BedReader` and `GffReader` iterate BED and GFF3/GTF files, yielding `BedEntry` /
`GffEntry` records (see the {doc}`loading data guide <./grove/loading_data>`).

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

### BamReader (SAM/BAM alignments)

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

### FastaReader (FASTA/FASTQ sequences)

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

### FastaIndex (random-access FASTA)

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

### VcfReader (VCF/BCF variants)

`VcfReader` is a single-pass iterator over VCF/BCF (plain, bgzip-ed, or binary BCF —
htslib auto-detects), yielding `VcfEntry`. Not thread-safe (one reader per thread);
the GIL is released around the htslib read.

```python
VcfReader(path, parse_info=True, parse_samples=True, skip_filtered=False)
```

Also: `get_header()`, `get_sample_names()`, `get_contigs()`, `get_error_message()`,
`get_current_line()`.

- **`VcfEntry`** fields: `chrom`, `start`/`end` (0-based half-open: `start = POS-1`,
  `end = start + len(REF)`), `id`, `ref`, `alt` (list), `qual` + `qual_missing`,
  `filter` (list), `info` (htslib-typed: bool for Flag, list[int]/list[float], str),
  `format` (FORMAT key order), `samples`. Predicates: `passed_filter()`, `is_snp()`,
  `is_indel()`, static `is_symbolic_allele(allele)`. Symbolic alleles (`<*>`,
  `<NON_REF>`, `*`) are kept verbatim in `alt` but excluded from is_snp/is_indel;
  monomorphic `ALT=.` yields an empty `alt`.
- **`VcfEntry.to_coordinate()`** -> an unstranded `GenomicCoordinate`;
  **`to_dict()`** -> a JSON payload. There is **no typed VcfGrove** (the record isn't
  serializable) — load variants into the universal `Grove` via these two.
- **`SampleGenotype`** (`.samples` items): `gt_alleles` (0=REF, 1..=ALT, -1=missing),
  `phased`, `has_gt`, `fields` (other FORMAT keys), plus `gt_string()` ("0/1", "0|1",
  "./.") and `is_hom_ref()`.

```python
import pygenogrove as pg
g = pg.Grove()
for v in pg.VcfReader("calls.vcf", skip_filtered=True):
    g.insert(v.chrom, v.to_coordinate(), v.to_dict())
    if v.is_snp():
        print(v.chrom, v.start, v.ref, v.alt, [s.gt_string() for s in v.samples])
```

### FiletypeDetector (format detection)

`FiletypeDetector` infers a file's format and compression from its extension
(compression extension stripped first) and magic bytes.

```python
import pygenogrove as pg

ftype, comp = pg.FiletypeDetector().detect_filetype("peaks.bed.gz")
# (Filetype.BED, CompressionType.GZIP)
```

- `detect_filetype(path) -> (Filetype, CompressionType)`
- `Filetype`: `BED` / `BEDGRAPH` / `GFF` / `GTF` / `VCF` / `SAM` / `BAM` /
  `FASTA` / `FASTQ` / `GG` / `UNKNOWN`. (`Filetype.VCF` is recognized for VCF/BCF
  inputs consumed by `VcfReader`.)
- `CompressionType`: `NONE` / `GZIP` / `BZIP2` / `XZ` / `ZSTD` / `LZ4` /
  `UNKNOWN`.

::::

:::::