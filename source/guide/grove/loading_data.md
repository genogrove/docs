# Loading Data from Files

Combine file readers from the `genogrove::io` namespace with grove insertion to load genomic data
directly from BED, GFF/GTF, and BAM/SAM files.

## BED Files

### Simple Loading (Incremental Insertion)

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
    try {
        for (const auto& entry : reader) {
            // BED files are typically sorted by position
            // Convert half-open [start, end) to closed [start, end]
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

### Efficient Loading (Bulk Insertion)

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
    try {
        for (const auto& entry : reader) {
            data[entry.chrom].emplace_back(
                gdt::interval(entry.start, entry.end - 1),
                entry.name.value_or("unknown"));
        }
    } catch (const std::runtime_error& e) {
        std::cerr << "Error: " << e.what() << "\n";
    }

    // Bulk insert per chromosome (data must be sorted)
    for (auto& [chrom, chrom_data] : data) {
        my_grove.insert_data(chrom, chrom_data, gst::sorted, gst::bulk);
    }

    std::cout << "Loaded " << my_grove.indexed_vertex_count() << " intervals using bulk insertion\n";

    return 0;
}
```

## GFF/GTF Files

```cpp
#include <genogrove/io/gff_reader.hpp>
#include <genogrove/structure/grove/grove.hpp>
#include <genogrove/data_type/interval.hpp>

namespace gio = genogrove::io;
namespace gdt = genogrove::data_type;
namespace gst = genogrove::structure;

int main() {
    gst::grove<gdt::interval, std::string> my_grove(100);

    gio::gff_reader reader("annotations.gff.gz");
    try {
        for (const auto& entry : reader) {
            my_grove.insert_data(entry.seqid,
                                gdt::interval(entry.start, entry.end - 1),
                                entry.get_gene_id().value_or(entry.type),
                                gst::sorted);
        }
    } catch (const std::runtime_error& e) {
        std::cerr << "Error: " << e.what() << "\n";
    }

    std::cout << "Loaded " << my_grove.indexed_vertex_count() << " features\n";

    return 0;
}
```

## BAM/SAM Files

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
    gio::bam_reader_options opts = gio::bam_reader_options::primary_only();
    opts.min_mapq = 20;
    gio::bam_reader reader("alignments.bam", opts);

    try {
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

## Key Points

- Readers produce 0-based half-open `[start, end)` coordinates; the grove uses closed `[start, end]` — subtract 1 from `end` when constructing `gdt::interval`
- File readers handle decompression automatically
- For small files, use incremental insertion with `sorted` tag
- For large files (>10K intervals), collect data and use bulk insertion with the `sorted` tag
- Data must be sorted before using bulk insertion (BED files are typically pre-sorted)
- Bulk insertion is ~10-20x faster for large datasets
- See the {doc}`/guide/performance` for detailed insertion strategies