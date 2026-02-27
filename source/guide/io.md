# Reading Genomic Files (I/O)

The `genogrove::io` namespace provides efficient readers for common genomic file formats with automatic compression detection.

## Reader Ownership

All file readers (`bed_reader`, `gff_reader`, `bam_reader`) own raw htslib resource pointers and are
**non-copyable** but **movable**. Attempting to copy a reader will produce a compile error.

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

## Automatic File Type Detection

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
- VCF (Variant Call Format)
- GG (Genogrove native format)

**Supported Compression Formats:**

- GZIP (.gz, including BGZF)
- BZIP2 (.bz2)
- XZ (.xz, LZMA)
- ZSTD (.zst)
- LZ4 (.lz4)

## BED Files

BED files store genomic intervals with optional metadata. The `bed_reader` provides iterator-based access:

```cpp
#include <genogrove/io/bed_reader.hpp>
#include <iostream>

namespace gio = genogrove::io;

int main() {
    // Automatically handles compressed files (.bed.gz)
    gio::bed_reader reader("example.bed");

    for (const auto& entry : reader) {
        std::cout << "Chromosome: " << entry.chrom << "\n"
                  << "Start: " << entry.interval.get_start() << "\n"
                  << "End: " << entry.interval.get_end() << "\n";

        // Optional fields (if present in file)
        if (entry.name) {
            std::cout << "Name: " << *entry.name << "\n";
        }
        if (entry.strand) {
            std::cout << "Strand: " << *entry.strand << "\n";
        }
    }

    return 0;
}
```

### Mixed BED Formats

The `bed_reader` supports files that mix BED3, BED6, and BED12 records. Optional fields are reset
on each record, so a BED6 line following a BED12 line will not carry over stale block or RGB data:

```cpp
gio::bed_reader reader("mixed.bed");

for (const auto& entry : reader) {
    // Always present (BED3)
    std::cout << entry.chrom << "\t"
              << entry.interval.get_start() << "\t"
              << entry.interval.get_end();

    // Only set on BED6+ lines
    if (entry.name)   std::cout << "\t" << *entry.name;
    if (entry.score)  std::cout << "\t" << *entry.score;
    if (entry.strand) std::cout << "\t" << *entry.strand;

    // Only set on BED12 lines
    if (entry.blocks)  std::cout << "\t(has blocks)";

    std::cout << "\n";
}
```

### BED Entry Fields

- `chrom` (std::string): Chromosome name
- `interval` (gdt::interval): Genomic interval (0-based, half-open)
- `name` (std::optional\<std::string>): Feature name
- `score` (std::optional\<int>): Score value
- `strand` (std::optional\<char>): Strand (+/-)
- `thickness` (std::optional\<thick_info>): Display thickness coordinates
- `item_rgb` (std::optional\<rgb_color>): RGB color value
- `blocks` (std::optional\<block_info>): Block information

## GFF/GTF Files

GFF3 and GTF files contain gene annotations. The `gff_reader` auto-detects the format variant
by inspecting the attribute column (GFF3 uses `key=value`, GTF uses `key "value"`).
Coordinates are 1-based inclusive in the file and converted to 0-based half-open intervals.

```cpp
#include <genogrove/io/gff_reader.hpp>
#include <iostream>

namespace gio = genogrove::io;

int main() {
    gio::gff_reader reader("annotations.gff");

    for (const auto& entry : reader) {
        std::cout << "Sequence: " << entry.seqid << "\n"
                  << "Type: " << entry.type << "\n"
                  << "Start: " << entry.interval.get_start() << "\n"
                  << "End: " << entry.interval.get_end() << "\n";

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

    return 0;
}
```

### GFF Entry Fields

- `seqid` (std::string): Chromosome/contig name
- `source` (std::string): Source of the feature
- `type` (std::string): Feature type (gene, exon, CDS, etc.)
- `interval` (gdt::interval): Genomic interval (0-based, half-open, converted from 1-based inclusive)
- `score` (std::optional\<double>): Score value (`std::nullopt` when `.` in file)
- `strand` (std::optional\<char>): Strand (+, -, ., or ?)
- `phase` (std::optional\<int>): Phase for CDS features (0, 1, or 2)
- `attributes` (std::map\<std::string, std::string>): Key-value pairs from column 9
- `format` (gff_format): Detected format — `gff_format::GFF3`, `gff_format::GTF`, or `gff_format::UNKNOWN`

### Attribute Access

Helper methods return `std::optional<std::string>` (or `std::optional<int>` for `get_exon_number()`).
Some helpers try multiple attribute keys to work across GFF3 and GTF conventions:

- `get_gene_id()` — returns `gene_id`
- `get_transcript_id()` — returns `transcript_id`
- `get_exon_number()` — parses `exon_number` as `int`
- `get_gene_name()` — tries `gene_name`, then falls back to GFF3's `Name`
- `get_gene_biotype()` — tries `gene_biotype`, `gene_type`, then `biotype`
- `get_attribute(key)` — generic getter for any attribute key

You can also access the attributes map directly:

```cpp
// Direct map access
auto it = entry.attributes.find("ID");
if (it != entry.attributes.end()) {
    std::cout << "ID: " << it->second << "\n";
}
```

### GTF Validation

When GTF format is detected, the reader enforces GTF requirements:
- `gene_id` is required on **all** features
- `transcript_id` is required on exon, CDS, start_codon, stop_codon, UTR, 5UTR, and 3UTR features

If validation fails, `read_next()` returns `false` and the error is available via `get_error_message()`.

### Convenience Methods

- `is_gtf()` — returns `true` if format is GTF
- `is_gff3()` — returns `true` if format is GFF3

## BAM/SAM Files

BAM, SAM, and CRAM files store sequence alignments. The `bam_reader` auto-detects the format and handles
decompression via htslib. SAM uses 1-based positions (POS); these are converted to 0-based half-open
intervals using the CIGAR string to compute the aligned reference length.

```cpp
#include <genogrove/io/bam_reader.hpp>
#include <iostream>

namespace gio = genogrove::io;

int main() {
    gio::bam_reader reader("alignments.bam");

    for (const auto& entry : reader) {
        std::cout << "Read: " << entry.qname << "\n"
                  << "Chrom: " << entry.chrom << "\n"
                  << "Start: " << entry.interval.get_start() << "\n"
                  << "End: " << entry.interval.get_end() << "\n"
                  << "Strand: " << entry.get_strand() << "\n"
                  << "MAPQ: " << static_cast<int>(entry.mapq) << "\n"
                  << "CIGAR: " << entry.cigar_string_repr() << "\n";

        if (entry.mate) {
            std::cout << "Mate chrom: " << entry.mate->chrom << "\n"
                      << "Mate pos: " << entry.mate->position << "\n"
                      << "Insert size: " << entry.mate->insert_size << "\n";
        }
    }

    return 0;
}
```

### Filtering Options

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

### SAM Entry Fields

- `qname` (std::string): Read name
- `chrom` (std::string): Reference sequence name
- `interval` (gdt::interval): Genomic interval (0-based, half-open, computed from POS + CIGAR)
- `flags` (alignment_flags): Bitwise flags with convenience methods (`is_paired()`, `is_reverse()`, `is_duplicate()`, etc.)
- `mapq` (uint8_t): Mapping quality
- `cigar` (cigar_string): CIGAR operations as a `std::vector<cigar_element>`
- `sequence` (std::string): Read sequence
- `quality` (std::string): ASCII quality scores
- `mate` (std::optional\<mate_info>): Mate information (`chrom`, `position`, `insert_size`)
- `tags` (sam_tags): Auxiliary tags (`std::unordered_map<std::string, sam_tag_value>`)

### CIGAR Operations

Each `cigar_element` has an `op` (operation code) and a `length`. Reference-consuming operations
(M, D, N, =, X) determine the aligned interval length.

```cpp
for (const auto& elem : entry.cigar) {
    std::cout << elem.length << elem.to_char();        // e.g. "50M2I30M"
    if (elem.consumes_reference()) { /* M, D, N, =, X */ }
    if (elem.consumes_query())     { /* M, I, S, =, X */ }
}
```

### Tag Access

Auxiliary tags are stored in an `std::unordered_map<std::string, sam_tag_value>`. The value is a
`std::variant` supporting `char`, `int64_t`, `float`, `std::string`, and typed vectors.

```cpp
auto it = entry.tags.find("NH");
if (it != entry.tags.end()) {
    int64_t num_hits = std::get<int64_t>(it->second);
    std::cout << "Number of hits: " << num_hits << "\n";
}
```

### Convenience Methods

- `get_strand()` — returns `'+'`, `'-'`, or `'.'`
- `is_primary()` — not secondary and not supplementary
- `is_mapped()` — not unmapped
- `cigar_string_repr()` — CIGAR as a human-readable string (e.g. `"50M2I30M"`)

