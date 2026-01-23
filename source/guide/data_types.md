# Working with Data Types

The `genogrove::data_type` namespace provides core genomic data types.

## Intervals

The `interval` class represents genomic regions using 0-based, half-open coordinates:

```cpp
#include <genogrove/data_type/interval.hpp>

namespace gdt = genogrove::data_type;

int main() {
    // Create intervals
    gdt::interval iv1{100, 200};  // [100, 200)
    gdt::interval iv2{150, 250};  // [150, 250)

    // Check for overlap
    if (gdt::interval::overlap(iv1, iv2)) {
        std::cout << "Intervals overlap\n";
    }

    // Comparison operators
    gdt::interval iv3{50, 75};
    if (iv3 < iv1) {
        std::cout << "iv3 comes before iv1\n";
    }

    // Aggregate multiple intervals
    std::vector<gdt::interval> intervals = {
        {100, 200}, {150, 250}, {300, 400}
    };
    auto merged = gdt::interval::aggregate(intervals);

    // String representation
    std::cout << iv1.to_string() << "\n";  // "[100, 200)"

    return 0;
}
```

**Interval Methods:**

- `overlap(a, b)` - Static method to check overlap
- `aggregate(intervals)` - Merge overlapping intervals
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
    if (gdt::genomic_coordinate::overlap(coord, other_coord)) {
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
