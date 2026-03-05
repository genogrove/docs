# Working with Data Types

The `genogrove::data_type` namespace provides core genomic data types.

## Common Interface

All data types in genogrove implement a shared interface:

- **Comparison operators**: `<`, `>`, `==`
- **Overlap detection**: Static method checking if two values intersect
- **Aggregation**: Combines multiple values into one result
- **Serialization/Deserialization**: Binary I/O operations
- **String representation**: Converts values to readable format

Constructors, comparison operators, getters/setters, and overlap detection are `constexpr`, so they
can be used in compile-time contexts:

```cpp
constexpr gdt::interval region{100, 200};
static_assert(region.get_start() == 100);
static_assert(gdt::interval::overlaps(region, gdt::interval{150, 250}));
```

## Intervals

The `interval` class represents genomic regions using closed `[start, end]` coordinates (both endpoints inclusive):

```cpp
#include <genogrove/data_type/interval.hpp>

namespace gdt = genogrove::data_type;

int main() {
    // Create intervals
    gdt::interval iv1{100, 200};  // [100, 200]
    gdt::interval iv2{150, 250};  // [150, 250]

    // Check for overlap
    if (gdt::interval::overlaps(iv1, iv2)) {
        std::cout << "Intervals overlap\n";
    }

    // Comparison operators
    gdt::interval iv3{50, 75};
    if (iv3 < iv1) {
        std::cout << "iv3 comes before iv1\n";
    }

    // Aggregate two intervals into one
    auto merged = gdt::interval::aggregate(iv1, iv2);

    // String representation
    std::cout << iv1.to_string() << "\n";  // "[100, 200]"

    return 0;
}
```

**Interval Methods:**

- `overlaps(a, b)` - Static method to check overlap
- `aggregate(a, b)` - Merge two intervals into their bounding interval
- Comparison: `<`, `>`, `==`
- `get_start()`, `set_start()`, `get_end()`, `set_end()`
- `to_string()` - String representation

## Genomic Coordinates

The `genomic_coordinate` class extends intervals with strand information:

```cpp
#include <genogrove/data_type/genomic_coordinate.hpp>

namespace gdt = genogrove::data_type;

int main() {
    // Create coordinate with strand
    gdt::genomic_coordinate coord{'+', 1000, 2000};

    // Access properties
    char strand = coord.get_strand();
    size_t start = coord.get_start();
    size_t end = coord.get_end();

    // Modify strand
    coord.set_strand('-');

    // All interval methods are available
    if (gdt::genomic_coordinate::overlaps(coord, other_coord)) {
        std::cout << "Coordinates overlap\n";
    }

    return 0;
}
```

## Keys and Associated Data

The `key` class wraps genomic types with optional associated data:

```cpp
#include <genogrove/data_type/key.hpp>
#include <genogrove/data_type/interval.hpp>

namespace gdt = genogrove::data_type;

struct GeneInfo {
    std::string name;
    double expression;
};

int main() {
    // Key with data
    gdt::key<gdt::interval, GeneInfo> gene_key(
        gdt::interval{100, 200},
        GeneInfo{"BRCA1", 45.3}
    );

    // Access key value
    auto interval = gene_key.get_value();

    // Access associated data
    auto info = gene_key.get_data();
    std::cout << "Gene: " << info.name << "\n";
    std::cout << "Expression: " << info.expression << "\n";

    // Check if key has data
    if (gene_key.has_data()) {
        std::cout << "Key has associated data\n";
    }

    return 0;
}
```

## Numeric

The `numeric` type provides integer wrapper semantics for point-based operations:

```cpp
#include <genogrove/data_type/numeric.hpp>

namespace gdt = genogrove::data_type;

int main() {
    // Create numeric values
    gdt::numeric n1{100};
    gdt::numeric n2{200};

    // Comparison uses standard integer ordering
    if (n1 < n2) {
        std::cout << "n1 comes before n2\n";
    }

    // Overlap occurs only when values are exactly equal
    gdt::numeric n3{100};
    if (gdt::numeric::overlaps(n1, n3)) {
        std::cout << "Values are equal\n";
    }

    // Aggregation returns the maximum of two values
    auto max_val = gdt::numeric::aggregate(n1, n2);  // Returns 200

    return 0;
}
```

**Numeric Characteristics:**

- Comparison: Standard integer ordering
- Overlap: Only when values are exactly equal
- Aggregation: Returns the maximum value

## K-mer

The `kmer` type represents DNA sequences using compact 2-bit encoding:

```cpp
#include <genogrove/data_type/kmer.hpp>

namespace gdt = genogrove::data_type;

int main() {
    // Create k-mer from DNA sequence
    gdt::kmer k1{"ACGT"};  // 4-mer
    gdt::kmer k2{"TGCA"};  // 4-mer

    // Comparison orders by k-value first, then encoding
    if (k1 < k2) {
        std::cout << "k1 comes before k2\n";
    }

    // Overlap requires exact sequence match
    gdt::kmer k3{"ACGT"};
    if (gdt::kmer::overlaps(k1, k3)) {
        std::cout << "K-mers are identical\n";
    }

    // String representation
    std::cout << k1.to_string() << "\n";  // "ACGT"

    return 0;
}
```

**K-mer Characteristics:**

- Encoding: 2-bit per nucleotide (A=00, C=01, G=10, T=11)
- Maximum length: 32 nucleotides (fits in 64-bit integer)
- Comparison: Orders by k-value first, then encoding
- Overlap: Exact sequence match required
- Aggregation: Returns k-mer with maximum encoding

```{toctree}
:maxdepth: 1

data_types/key
data_types/data_registry
```
