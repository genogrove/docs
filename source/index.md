% genogrove documentation master file, created by
% sphinx-quickstart on Wed Aug 20 17:14:01 2025.
% You can adapt this file completely to your liking, but it should at least
% contain the root `toctree` directive.

# genogrove

A high-performance modern C++ library for genomic data structures and interval queries.

## Overview

Genogrove provides a specialized B+ tree data structure (the **grove**) optimized for storing and querying genomic intervals. It combines efficient interval overlap detection with an embedded graph overlay for representing relationships between genomic features.

**Key Features:**

- **Flexible Key Types**: Works with any type satisfying the `key_type_base` concept (built-in: `interval`, `genomic_coordinate`)
- **Multi-Index Organization**: Separate trees per chromosome for efficient queries
- **Sorted Insertion**: O(1) amortized insertion for pre-sorted genomic data
- **Graph Overlay**: Link keys within the grove to represent feature relationships
- **File I/O**: Automatic format detection and compression support (BED, GFF/GTF, VCF)
- **Modern C++20**: Type-safe, concept-based design

## Quick Example

Here's a complete example showing file reading, storage, and querying:

```cpp
#include <genogrove/io/bed_reader.hpp>
#include <genogrove/structure/grove/grove.hpp>
#include <genogrove/data_type/interval.hpp>

namespace gio = genogrove::io;
namespace gdt = genogrove::data_type;
namespace gst = genogrove::structure;

int main() {
    // Create grove to store genomic features
    gst::grove<gdt::interval, std::string> features(100);

    // Read BED file (handles .bed.gz automatically)
    gio::bed_reader reader("genes.bed.gz");

    for (const auto& entry : reader) {
        // Insert sorted by chromosome
        features.insert_data(
            entry.chrom,
            entry.interval,
            entry.name,
            gst::sorted  // Optimized for pre-sorted data
        );
    }

    // Query for overlapping features
    gdt::interval query{1000, 2000};
    auto results = features.intersect(query, "chr1");

    std::cout << "Found " << results.get_keys().size()
              << " overlapping features\n";

    return 0;
}
```

## Why Genogrove?

**Performance**

: Optimized B+ tree implementation with O(1) sorted insertion and efficient overlap queries.

**Flexibility**

: Use built-in genomic types or define custom key types for specialized applications.

**Graph Integration**

: Represent complex relationships (transcripts, regulatory networks) alongside spatial queries.

**Modern Design**

: C++20 concepts, type safety, and zero-cost abstractions.

## Requirements

- **Compiler**: C++20 compatible (GCC 12+, Clang 14+, MSVC 2022+)
- **Build System**: CMake 3.15 or higher
- **Dependencies**: htslib (for compressed file support)

## Getting Started

Ready to use genogrove? Check out the {doc}`user_guide` for:

- Installation instructions
- Detailed tutorials on I/O operations
- Working with data types and the grove
- Complete examples and best practices

## Documentation

{doc}`user_guide`

: Comprehensive tutorials and examples

{doc}`reference/index`

: Complete API reference

GitHub Repository

: [genogrove on GitHub](https://github.com/genogrove/genogrove)

## Community

- **Issues**: Report bugs and request features on [GitHub Issues](https://github.com/genogrove/genogrove/issues)
- **Discussions**: Ask questions and share ideas on [GitHub Discussions](https://github.com/genogrove/genogrove/discussions)

## License

Genogrove is distributed under the [MIT License](https://opensource.org/licenses/MIT).

```{toctree}
:caption: Documentation
:hidden: true
:maxdepth: 2

self
user_guide
reference/index
cli
```
