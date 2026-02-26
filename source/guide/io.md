# Reading Genomic Files (I/O)

The `genogrove::io` namespace provides efficient readers for common genomic file formats with automatic compression detection.

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

**BED Entry Fields:**

- `chrom` (std::string): Chromosome name
- `interval`: (genogrove::data_type::interval) Genomic interval (0-based, half-open)
- `name` (std::optional\<std::string>): Feature name
- `score` (std::optional\<int>): Score value
- `strand` (std::optional\<char>): Strand (+/-)
- `thickness` (std::optional\<thick_info>): Display thickness coordinates
- `item_rgb` (std::optional\<rgb_color>): RGB color value
- `blocks` (std::optional\<block_info>): Block information

## GFF/GTF Files

GFF3 and GTF files contain gene annotations. Genogrove automatically detects the format variant:

```cpp
#include <genogrove/io/gff_reader.hpp>

namespace gio = genogrove::io;

int main() {
    gio::gff_reader reader("annotations.gff");

    for (const auto& entry : reader) {
        std::cout << "Sequence: " << entry.seqid << "\n"
                  << "Type: " << entry.type << "\n"
                  << "Start: " << entry.interval.get_start() << "\n"
                  << "End: " << entry.interval.get_end() << "\n";

        // GFF/GTF entries are 1-based but converted to 0-based intervals

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

**GFF Entry Fields:**

- `seqid` (string): Chromosome/contig name
- `source` (string): Source of feature
- `type` (string): Feature type (gene, exon, CDS, etc.)
- `interval`: Genomic interval (converted to 0-based)
- `score` (optional): Score value
- `strand` (optional): Strand (+, -, ., or ?)
- `phase` (optional): Phase for CDS features (0, 1, 2)
- `attributes` (map): Key-value pairs from column 9
- `format`: Detected format (GFF3 or GTF)

**Helper Methods for Attributes:**

- `get_gene_id()` - Extract gene_id
- `get_transcript_id()` - Extract transcript_id
- `get_exon_number()` - Extract exon_number
- `get_gene_name()` - Extract gene_name
- `get_gene_biotype()` - Extract gene_biotype/gene_type
- `get_attribute(key)` - Generic attribute getter

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

## Loading Files into a Grove

Combine file readers with grove insertion to load genomic data:

**Simple Loading (Incremental Insertion)**

```cpp
#include <genogrove/io/bed_reader.hpp>
#include <genogrove/structure/grove/grove.hpp>
#include <genogrove/data_type/interval.hpp>

namespace gio = genogrove::io;
namespace gdt = genogrove::data_type;
namespace gst = genogrove::structure;

int main() {
    gst::grove<gdt::interval, std::string> my_grove(100);

    // Read and insert each entry
    gio::bed_reader reader("genes.bed.gz");
    for (const auto& entry : reader) {
        // BED files are typically sorted by position
        my_grove.insert_data(entry.chrom, entry.interval,
                            entry.name.value_or("unknown"),
                            gst::sorted);
    }

    std::cout << "Loaded " << my_grove.indexed_vertex_count() << " intervals\n";

    // Query the loaded data
    auto results = my_grove.intersect(gdt::interval{1000, 2000}, "chr1");
    std::cout << "Found " << results.get_keys().size() << " overlapping intervals\n";

    return 0;
}
```

**Efficient Loading (Bulk Insertion)**

For large files (>10K intervals), use bulk insertion for better performance:

```cpp
#include <genogrove/io/bed_reader.hpp>
#include <genogrove/structure/grove/grove.hpp>
#include <genogrove/data_type/interval.hpp>
#include <map>
#include <vector>

namespace gio = genogrove::io;
namespace gdt = genogrove::data_type;
namespace gst = genogrove::structure;

int main() {
    gst::grove<gdt::interval, std::string> my_grove(100);

    // Group entries by chromosome
    std::map<std::string, std::vector<std::pair<gdt::interval, std::string>>> data;

    gio::bed_reader reader("large_dataset.bed.gz");
    for (const auto& entry : reader) {
        data[entry.chrom].emplace_back(entry.interval, entry.name.value_or("unknown"));
    }

    // Bulk insert per chromosome (data must be sorted)
    for (auto& [chrom, chrom_data] : data) {
        my_grove.insert_data(chrom, chrom_data, gst::sorted, gst::bulk);
    }

    std::cout << "Loaded " << my_grove.indexed_vertex_count() << " intervals using bulk insertion\n";

    return 0;
}
```

**Loading BAM Reads into a Grove**

```cpp
#include <genogrove/io/bam_reader.hpp>
#include <genogrove/structure/grove/grove.hpp>
#include <genogrove/data_type/interval.hpp>

namespace gio = genogrove::io;
namespace gdt = genogrove::data_type;
namespace gst = genogrove::structure;

int main() {
    gst::grove<gdt::interval, std::string> my_grove(100);

    // Read only high-quality primary alignments
    gio::bam_reader reader("alignments.bam",
                           gio::bam_reader_options::high_quality(20));

    for (const auto& entry : reader) {
        my_grove.insert_data(entry.chrom, entry.interval,
                             entry.qname, gst::sorted);
    }

    std::cout << "Loaded " << my_grove.indexed_vertex_count() << " reads\n";

    return 0;
}
```

**Key Points:**

- File readers handle decompression automatically
- For small files, use incremental insertion with `sorted` tag
- For large files (>10K intervals), collect data and use bulk insertion with the `sorted` tag
- Data must be sorted before using bulk insertion (BED files are typically pre-sorted)
- Bulk insertion is ~10-20x faster for large datasets
- See the Performance Guide for detailed insertion strategies
