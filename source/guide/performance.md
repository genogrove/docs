# Performance Optimization

## Tips for Optimal Performance

### Choose Appropriate Tree Order

The tree order parameter significantly affects performance:

- **Small datasets** (< 10K intervals): order = 50-100
- **Medium datasets** (10K-1M intervals): order = 100-500
- **Large datasets** (> 1M intervals): order = 500-1000

Higher order values provide:

- Better cache locality (fewer cache misses)
- Reduced tree height (fewer levels to traverse)
- More keys per node (better for sequential access)

```cpp
// For a large genomic dataset
gst::grove<gdt::interval, std::string> my_grove(500);
```

### Use Sorted Insertion for Pre-sorted Data

When data is already sorted (common for BED/GFF files), use sorted insertion:

```cpp
// For sorted data (e.g., BED files)
grove.insert_data(index, interval, data, gst::sorted);  // Much faster!

// For unsorted data
grove.insert_data(index, interval, data, gst::unsorted);  // Default
```

Sorted insertion provides O(1) amortized insertion time vs O(log n) for unsorted.

### Use Bulk Insertion for Large Datasets

For loading large datasets (>10K intervals), bulk insertion provides dramatic performance improvements:

```cpp
std::vector<gdt::interval> intervals = load_intervals();
std::vector<std::string> data = load_data();

// Bulk insertion - ~10-20x faster than incremental
// Data must be sorted before calling this function
grove.insert_data("chr1", intervals, data, gst::sorted, gst::bulk);
```

**Runtime Characteristics:**

- **Empty index**: O(n) bottom-up tree construction

  - Builds fully-packed leaf nodes (order-1 keys per node)
  - Then constructs internal layers
  - \~10-20x faster than incremental insertion
  - Better space utilization: 75-90% full nodes vs ~50% from splits

- **Existing data**: Appends to rightmost node

  - **CRITICAL**: All new keys must be strictly greater than existing keys
  - Throws `std::runtime_error` if violated

**Performance Comparison (1M intervals, empty index):**

| Method                 | Time          | Node Utilization   |
| ---------------------- | ------------- | ------------------ |
| Incremental (unsorted) | 10-20 seconds | ~50% (from splits) |
| Sorted insertion       | 2-5 seconds   | ~50% (from splits) |
| Bulk insertion         | 0.5-1 second  | 75-90% (packed)    |

**When to Use Bulk Insertion:**

- Initial loading of large genomic files (BED, GFF, GTF)
- Datasets with >10K intervals per chromosome
- When maximum performance is required
- Building indices for production use
- **Important**: Data must be sorted before using bulk insertion

### Organize by Chromosome

Always use chromosome/contig names as the index parameter:

```cpp
// Good - organized by chromosome
grove.insert_data("chr1", interval, data);
grove.insert_data("chr2", interval, data);

// Bad - all data in one tree
grove.insert_data("all", interval, data);
```

Benefits:

- Efficient chromosome-specific queries
- Reduced tree traversal for most genomic queries
- Better memory locality for same-chromosome data

## Compression Support

### Choosing the Right Compression Format

Different compression formats have different trade-offs:

**BGZF/GZIP (.gz)**

- Standard for genomic files
- Supports random access (BGZF)
- Good compression ratio
- Use for: BED, GFF, VCF files

**ZSTD (.zst)**

- Best compression ratio
- Fast decompression
- Use for: Long-term storage, archives

**LZ4 (.lz4)**

- Fastest decompression
- Lower compression ratio
- Use for: Temporary files, fast processing

**Example:**

```cpp
// All these are automatically handled
gio::bed_reader reader1("data.bed.gz");    // BGZF
gio::bed_reader reader2("data.bed.zst");   // ZSTD
gio::bed_reader reader3("data.bed.lz4");   // LZ4
gio::bed_reader reader4("data.bed");       // Uncompressed
```

## Memory Management

### Efficient Memory Usage

The grove uses a deque for key storage, providing:

- Stable pointers (required for graph overlay)
- Better cache locality than individual allocations
- Automatic memory management

```cpp
// Keys are automatically managed
auto* key = grove.insert_data("chr1", interval, data);
// Pointer remains valid until grove is destroyed
```

### Graph Overlay Considerations

When using graph overlays, consider:

- Edges are stored separately from the tree structure
- Each edge stores a pointer to target key
- Memory usage: O(E) where E is number of edges

```cpp
// Clear graph if no longer needed
grove.clear_graph();  // Frees edge memory, keeps keys
```

## Serialization

Save and load grove structures for faster startup:

```cpp
#include <fstream>

// Save grove to disk
{
    std::ofstream out("grove_data.bin", std::ios::binary);
    my_grove.serialize(out);
}

// Load grove from disk (implementation in progress)
{
    std::ifstream in("grove_data.bin", std::ios::binary);
    auto loaded_grove = gst::grove<gdt::interval, std::string>::deserialize(in);
}
```

**Note:** Serialization saves:

- Tree structure
- All keys and data
- Order parameter

**Not saved:**

- Graph edges (must be rebuilt)
- Rightmost node cache (recalculated on load)

## Query Optimization

### Chromosome-Specific Queries

Always specify the chromosome when possible:

```cpp
// Fast - searches only chr1 tree
auto results = grove.intersect(query, "chr1");

// Slower - searches all chromosomes
auto all_results = grove.intersect(query);
```

### Result Processing

Process query results efficiently:

```cpp
auto results = grove.intersect(query, "chr1");

// Get keys once
const auto& keys = results.get_keys();

// Process without repeated calls
for (auto* key : keys) {
    process(key);
}
```

## Benchmarking

Example benchmark for insertion:

```cpp
#include <chrono>
#include <iostream>

void benchmark_insertion() {
    gst::grove<gdt::interval, std::string> grove(100);

    const int N = 1000000;
    auto start = std::chrono::high_resolution_clock::now();

    for (int i = 0; i < N; ++i) {
        grove.insert_data(
            "chr1",
            gdt::interval{i * 100, i * 100 + 50},
            "feature" + std::to_string(i),
            gst::sorted  // Data is sorted
        );
    }

    auto end = std::chrono::high_resolution_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(
        end - start
    );

    std::cout << "Inserted " << N << " intervals in "
              << duration.count() << " ms\n";
    std::cout << "Rate: " << (N / (duration.count() / 1000.0))
              << " insertions/second\n";
}
```

## Best Practices Summary

1. **Choose appropriate tree order** based on dataset size
2. **Use bulk insertion** for large datasets (>10K intervals)
3. **Use sorted insertion** for pre-sorted incremental data
4. **Organize by chromosome** for efficient queries
5. **Use BGZF compression** for genomic files
6. **Specify chromosome** in queries when possible
7. **Clear graph** when edges are no longer needed
8. **Serialize** large groves for faster loading
9. **Benchmark** your specific use case
