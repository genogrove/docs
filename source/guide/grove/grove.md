# Grove

The `grove` is a specialized B+ tree optimized for genomic interval storage and querying. It organizes data by index (e.g., chromosome) and supports efficient overlap queries. An embedded graph overlay allows you to create directed edges between keys, representing relationships between genomic features.

Beyond the core data structure covered on this page, the grove also supports:

- **{doc}`graph`** — Create directed edges between keys to represent relationships such as transcript structures or gene regulatory networks
- **{doc}`graph_manipulation`** — Inspect, modify, and analyze the graph structure with operations for edge management, neighbor traversal, and graph statistics
- **{doc}`loading_data`** — Load genomic data from BED, GFF/GTF, and BAM/SAM files directly into a grove

## Key Types and the key_type_base Concept

The grove is highly flexible and can work with any key type that satisfies the `key_type_base` concept. Genogrove provides four built-in key types:

- `interval` - Basic genomic intervals (closed `[start, end]`)
- `genomic_coordinate` - Intervals with strand information
- `numeric` - Single numerical value
- `kmer` - Single k-mer value

**Custom Key Types**

You can use any custom type as a key in the grove, as long as it satisfies the `key_type_base` concept requirements:

```cpp
// Required operations for key_type_base concept:
// 1. Comparison operators: <, >, ==
// 2. Static overlap detection: overlaps(a, b) -> bool
// 3. Static pairwise aggregation: aggregate(a, b) -> T
// 4. String representation: to_string() -> string
```

Example of a custom key type:

```cpp
#include <genogrove/data_type/key_type_base.hpp>

struct CustomInterval {
    size_t start;
    size_t end;
    int priority;

    // Comparison operators
    bool operator<(const CustomInterval& other) const {
        return start < other.start;
    }

    bool operator>(const CustomInterval& other) const {
        return start > other.start;
    }

    bool operator==(const CustomInterval& other) const {
        return start == other.start && end == other.end;
    }

    // Static overlap method
    static bool overlaps(const CustomInterval& a, const CustomInterval& b) {
        return !(a.end <= b.start || b.end <= a.start);
    }

    // Static pairwise aggregate method
    static CustomInterval aggregate(const CustomInterval& a, const CustomInterval& b) {
        return {std::min(a.start, b.start), std::max(a.end, b.end), 0};
    }

    // String representation
    std::string to_string() const {
        return "[" + std::to_string(start) + ", " +
               std::to_string(end) + ") p=" + std::to_string(priority);
    }
};

// Now you can use it with grove
gst::grove<CustomInterval, std::string> my_grove(100);
```

## Creating a Grove

Create a grove with specified template parameters and tree order:

```cpp
#include <genogrove/structure/grove/grove.hpp>
#include <genogrove/data_type/interval.hpp>

namespace gdt = genogrove::data_type;
namespace gst = genogrove::structure;

int main() {
    // grove<key_type, data_type, edge_data_type>(order)
    // Order determines max keys per node (higher = more cache-friendly)
    // Order must be >= 3 (throws std::invalid_argument otherwise)

    // Using built-in interval type
    gst::grove<gdt::interval, std::string> grove1(100);

    // Using genomic_coordinate (with strand)
    gst::grove<gdt::genomic_coordinate, std::string> grove2(100);

    // Default-constructed grove uses order 3
    gst::grove<gdt::interval, std::string> grove3;

    return 0;
}
```

**Template Parameters:**

- `key_type`: Type satisfying `key_type_base` concept (interval, genomic_coordinate, or custom)
- `data_type`: Associated data type (default: void for no data)
- `edge_data_type`: Edge metadata for graph overlay (default: void)

**Constructor Parameters:**

- `order` (int): Maximum children per node (and `order - 1` keys). Must be `>= 3`; throws
  `std::invalid_argument("grove order must be >= 3")` otherwise. Order 2 is degenerate — internal
  splits with `order == 2` would produce a sibling with zero keys, which classical B+ trees forbid.
  The default constructor (`grove()`) uses order 3.

## Ownership Semantics

`grove` (and its internal `node` type) is **non-copyable and move-only**. Copy construction and
copy assignment are deleted because these types own raw pointers internally—a shallow copy would
cause a double-free. Move operations are provided, so you can return a grove from a function or
store it in a container:

```cpp
// OK — move construction
auto loaded = gst::grove<gdt::interval, std::string>::deserialize(in);

// OK — pass by reference
void process(gst::grove<gdt::interval, std::string>& g);

// OK — move into a container
std::vector<gst::grove<gdt::interval, std::string>> groves;
groves.push_back(std::move(my_grove));

// ERROR — copy is deleted
// auto copy = my_grove;                   // won't compile
// void f(gst::grove<gdt::interval, std::string> g);  // won't compile (pass-by-value copies)
```

Always pass groves by reference or move them explicitly with `std::move`.

## Accessing Indices

Use `get_root_nodes()` to access the grove's index map (chromosome → root node). It returns a
**const reference** to the internal `std::unordered_map`, so use `.at()` or `.find()` for lookups
(not `operator[]`, which requires a non-const map). The reference is valid only while the grove is
alive and unmodified.

```cpp
const auto& roots = my_grove.get_root_nodes();
if (auto it = roots.find("chr1"); it != roots.end()) {
    // it->second is the root node for chr1
}
```

`set_root_nodes()` is private — indices are created automatically on first insertion.

## Inserting Data

The grove supports multiple insertion modes with multi-index organization:

```cpp
#include <genogrove/structure/grove/grove.hpp>
#include <genogrove/data_type/interval.hpp>

namespace gdt = genogrove::data_type;
namespace gst = genogrove::structure;

int main() {
    gst::grove<gdt::interval, std::string> my_grove(100);

    // Insert with index (e.g., chromosome name)
    // Returns pointer to inserted key
    auto* key1 = my_grove.insert_data("chr1",
                                      gdt::interval{100, 200},
                                      "gene1");

    auto* key2 = my_grove.insert_data("chr1",
                                      gdt::interval{150, 250},
                                      "gene2");

    // Insert on different chromosome
    auto* key3 = my_grove.insert_data("chr2",
                                      gdt::interval{300, 400},
                                      "gene3");

    // Optimized insertion for pre-sorted data
    auto* key4 = my_grove.insert_data("chr1",
                                      gdt::interval{500, 600},
                                      "gene4",
                                      gst::sorted);  // Much faster!

    return 0;
}
```

**Insertion Modes:**

- `unsorted` (default): Full tree traversal for random data
- `sorted`: Optimized O(1) insertion for pre-sorted data
- `bulk`: Bulk insertion using hybrid bottom-up/append approach

**Multi-Index Organization:**

- Each index (e.g., chromosome) maintains a separate B+ tree
- Enables efficient chromosome-specific queries
- Automatic index creation on first insertion

## Bulk Insertion

For loading large datasets efficiently, use bulk insertion. Bulk insertion uses a hybrid bottom-up/append approach that is significantly faster than incremental insertion.

**How It Works:**

- **Empty index**: Builds tree from bottom-up (O(n) time)

  - Creates fully-packed leaf nodes first
  - Then builds internal layers
  - \~10-20x faster than incremental insertion for large datasets
  - Better space utilization: 75-90% full nodes vs ~50% from split-based insertion

- **Existing data**: Appends to rightmost node

  - **CRITICAL PRECONDITION**: All new keys must be strictly greater than existing keys in the index
  - Throws `std::runtime_error` if precondition is violated

**Usage:**

```cpp
#include <genogrove/structure/grove/grove.hpp>
#include <genogrove/data_type/interval.hpp>
#include <vector>

namespace gdt = genogrove::data_type;
namespace gst = genogrove::structure;

int main() {
    gst::grove<gdt::interval, std::string> my_grove(100);

    // Prepare sorted data as a container of (key, data) pairs
    std::vector<std::pair<gdt::interval, std::string>> data = {
        {{100, 200}, "gene1"}, {{300, 400}, "gene2"}, {{500, 600}, "gene3"}
    };

    // Bulk insert with sorted data (fastest method)
    my_grove.insert_data("chr1", data, gst::sorted, gst::bulk);

    return 0;
}
```

**Performance Comparison:**

For loading 1M intervals into an empty index:

- **Incremental insertion** (`unsorted`): ~10-20 seconds
- **Sorted insertion** (`sorted`): ~2-5 seconds
- **Bulk insertion** (`sorted, bulk`): ~0.5-1 second

**When to Use Bulk Insertion:**

- Loading pre-sorted genomic files (BED, GFF, GTF)
- Initial data loading into empty groves
- Datasets with >10K intervals per chromosome
- When maximum performance is required

**Important Notes:**

- **Data must be sorted** before calling bulk insertion
- Bulk insertion is most beneficial for datasets >10K intervals
- When appending to existing data, ensure new keys are strictly greater than all existing keys in that index
- Genomic files (BED, GFF, GTF) are typically pre-sorted by position

## Removing Keys

Use `remove_key()` to remove a previously-inserted key from the B+ tree. The method takes the
index name (e.g., chromosome) and a pointer to the key — typically one that was returned from
`insert_data()` or looked up via `intersect()`.

```cpp
gst::grove<gdt::interval, std::string> my_grove(100);

auto* k = my_grove.insert_data("chr1", gdt::interval{100, 200}, "gene1", gst::sorted);

// Remove the key. Returns true if found and removed, false otherwise.
bool removed = my_grove.remove_key("chr1", k);
```

**Behaviour:**

- Returns `true` if the key was found and removed, `false` otherwise (unknown index, null pointer,
  or key not present in the index's tree).
- Handles leaf underflow via borrow-from-sibling, merge, cascading rebalance, and root collapse —
  the tree stays balanced automatically.
- **Graph edges are cleaned up automatically**: all incoming and outgoing edges for the removed
  key are dropped, so callers never need to call `remove_edge`/`remove_edges_from`/`remove_edges_to`
  manually after `remove_key`.
- The key object itself is *not* deallocated — it remains in the grove's internal deque so that
  pointer stability is preserved. It is simply unlinked from the tree and graph. Call
  [`compact()`](#reclaiming-removed-key-storage-compact) to reclaim the slots when the dead
  storage adds up.

```cpp
// Example: prune genes that fall below a coverage threshold
auto results = my_grove.intersect(gdt::interval{0, 1000000}, "chr1");
for (auto* key : results.get_keys()) {
    if (coverage_of(key) < min_coverage) {
        my_grove.remove_key("chr1", key);
    }
}
```

### Reclaiming removed-key storage (`compact`)

`remove_key()` unlinks keys from the tree but **does not free** the underlying `key<>` objects
in the grove's internal deque. Across many insert/remove cycles the deque grows without bound
while `indexed_vertex_count()` decreases — invisible to public counters. `compact()` is the
caller-controlled, transactional rebuild that reclaims that memory.

```cpp
gst::grove<gdt::interval, std::string> my_grove(100);

// ... many insert / remove cycles ...

std::cout << "Live indexed keys: "   << my_grove.indexed_vertex_count() << "\n";
std::cout << "Deque slots in use: "  << my_grove.key_storage_size()     << "\n";

if (my_grove.key_storage_size() > 2 * my_grove.indexed_vertex_count()) {
    my_grove.compact();   // O(N + E); rebuilds key_storage, rewrites graph adjacency
}
```

**Behaviour:**

- **O(N + E)** — single pre-order walk of every tree to migrate keys + a single pass over the
  graph adjacency map to remap pointers.
- **Invalidates every indexed-key pointer** previously returned by `insert_data()`, query
  results, or `get_neighbors()`. Callers must rediscover keys via queries after compaction.
- **External keys are unaffected.** Pointers returned by `add_external_key()` and any graph
  edges referring to them remain valid.

Use `key_storage_size()` to decide when compaction is worth running. The value strictly grows
with internal separator keys (a healthy property of B+ trees) and with `remove_key()` calls;
compaction is only useful once the latter starts dominating.

```cpp
// Typical pattern: bulk-remove, then compact when no callers hold stale pointers
for (auto* k : victims) my_grove.remove_key("chr1", k);
// ... ensure no callers still hold `k` pointers ...
my_grove.compact();
```

## Querying Intervals

Find all intervals that overlap with a query region:

```cpp
#include <genogrove/structure/grove/grove.hpp>
#include <genogrove/data_type/interval.hpp>

namespace gdt = genogrove::data_type;
namespace gst = genogrove::structure;

int main() {
    gst::grove<gdt::interval, std::string> my_grove(100);

    // Insert some intervals
    my_grove.insert_data("chr1", gdt::interval{100, 200}, "gene1");
    my_grove.insert_data("chr1", gdt::interval{150, 250}, "gene2");
    my_grove.insert_data("chr1", gdt::interval{300, 400}, "gene3");
    my_grove.insert_data("chr2", gdt::interval{100, 200}, "gene4");

    // Query specific chromosome (temporaries work directly)
    auto results = my_grove.intersect(gdt::interval{175, 225}, "chr1");

    // Process results — get_keys() returns pointers to keys owned by the grove.
    for (auto* key : results.get_keys()) {
        std::cout << "Found: " << key->get_data()
                  << " at " << key->get_value().to_string() << "\n";
    }
    // Output: gene1, gene2 (gene3 doesn't overlap)

    // Query across all chromosomes
    auto all_results = my_grove.intersect(gdt::interval{175, 225});
    std::cout << "Total matches: " << all_results.get_keys().size() << "\n";

    return 0;
}
```

**Query Features:**

- Efficient overlap-based searching using B+ tree structure
- Index-specific queries (single chromosome) — `index` parameter accepts `std::string_view`
- Global queries (all chromosomes)
- Accepts temporaries and named variables (const reference parameter)
- Returns `query_result` containing matching keys

**Result type:**

`query_result::get_keys()` returns `const std::vector<key<...>*>&` — pointers to keys owned by
the grove, suitable for feeding directly into mutating graph operations such as `add_edge` or
`link_if` without a `const_cast`. The container template `query_result<key_type, data_type>` is
constrained with the `key_type_base` concept, so misuse with a non-conforming type fails at the
result-container instantiation site with a clean concept diagnostic instead of a deep template
instantiation error inside `key<>`.

```{warning}
Mutating a key's value via `key::set_value(...)` corrupts B+ tree ordering invariants. The same
risk exists through the pointer returned by `insert_data()`, so the convention is enforced by
discipline rather than at the API level — only mutate the *data* payload through these
pointers, never the key value.
```

For the closest features on each side of a query (rather than features overlapping
it), see [Flanking-Key Queries](#flanking-key-queries) below.

**Concept Constraints:**

The grove uses C++20 concepts to provide clear compile-time errors:

- `link_if(keys, predicate)` requires `std::invocable<Predicate, key*, key*>`
- `get_neighbors_if(source, predicate)` requires `std::predicate<Predicate, const edge_data_type&>`
- `insert_data(index, data, sorted, bulk)` and `build_tree_bottom_up`: `Container` must satisfy `std::ranges::forward_range` and `std::ranges::sized_range`
- `insert_data(index, data, bulk)`: `Container` must satisfy `std::ranges::random_access_range` and `std::ranges::sized_range`

## Flanking-Key Queries

In addition to `intersect()`, which finds keys that overlap a query, the grove supports a
`flanking()` query that returns the **predecessor** and **successor** of a query — the
two nearest non-overlapping keys that bracket it in sort order. This is useful when the
caller needs the closest features on each side of a position rather than the features
covering it (for example, the upstream and downstream genes of an enhancer).

```cpp
#include <genogrove/structure/grove/grove.hpp>
#include <genogrove/data_type/interval.hpp>

namespace gdt = genogrove::data_type;
namespace gst = genogrove::structure;

// flanking() works on any populated grove regardless of how it was built —
// `gst::sorted` here is just for parity with surrounding examples.
gst::grove<gdt::interval, std::string> g(100);
g.insert_data("chr1", gdt::interval{100, 200}, "A", gst::sorted);
g.insert_data("chr1", gdt::interval{500, 600}, "B", gst::sorted);
g.insert_data("chr1", gdt::interval{900, 1000}, "C", gst::sorted);

auto r = g.flanking(gdt::interval{650, 700}, "chr1");

if (auto* pred = r.get_predecessor()) {
    // "B" — largest non-overlapping key < query
}
if (auto* succ = r.get_successor()) {
    // "C" — smallest non-overlapping key > query
}
```

Each field of the returned `flanking_query_result` may be `nullptr` if no such
key exists (for example, the query is past the rightmost key, or the index does
not exist). Returned pointers reference keys owned by the grove and remain valid
as long as the referenced key is not removed. Like `query_result`,
`flanking_query_result<key_type, data_type>` is constrained with the
`key_type_base` concept so non-conforming `key_type` arguments fail at the
result-container instantiation site.

**Selection rule.** Keys that satisfy `key_type::overlaps(K, query)` are
excluded by definition. Among the remaining candidates:

- For interval-like keys (`interval`, `genomic_coordinate`), the predecessor is the key
  with the largest `end` below `query.start` (smallest left-side gap), and the successor
  is the key with the smallest `start` above `query.end` (smallest right-side gap). For
  nested intervals these can differ from the sort-order extremum — e.g., between `[50, 100]`
  and `[80, 90]`, sort picks `[80, 90]` but `[50, 100]` is closer to a query at `[150, …]`.
- For scalar keys (`numeric`, `kmer`), nearest-by-value coincides with the sort-order
  extremum, so the predecessor/successor are simply the closest values on each side.

**Distance is computed by the caller** because it is type-specific. For closed-coord
intervals: `query.start - predecessor->get_value().get_end() - 1`; for numeric scalars:
`query.value - predecessor->get_value()`.

### Filtering by a Predicate

A second overload accepts a binary predicate `is_compatible(candidate, query)` that
filters candidates before the overlap and ordering checks. Use this to express
domain-specific constraints that are not encoded in `key_type::overlaps()` — for
example, restricting the search to same-strand neighbors when keys carry strand
information:

```cpp
// Assumes a grove parameterised with genomic_coordinate (which carries strand);
//   gst::grove<gdt::genomic_coordinate, /* data */> grove(...);
//   gdt::genomic_coordinate q{...};
auto r = grove.flanking(q, "chr1",
    [](const auto& candidate, const auto& q) {
        return q.get_strand() == '*' || candidate.get_strand() == '*'
            || candidate.get_strand() == q.get_strand();
    });
```

The `get_strand()` calls assume `genomic_coordinate` keys; for plain `interval`
keys (no strand), use a predicate that inspects whatever metadata your key
type exposes.

The predicate is invoked at leaf level only. Internal-node pruning is purely
structural (based on aggregate ranges) and never consults the predicate, so
subtrees that contain only incompatible keys are still visited but filtered
out at the leaves.

```{note}
`flanking()` is named to avoid collision with the graph-overlay `get_neighbors()`,
which returns graph-edge-connected keys — a distinct concept from spatial nearest
neighbors.
```

```{toctree}
:maxdepth: 1

graph
graph_manipulation
loading_data
```
