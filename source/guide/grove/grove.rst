Using the Grove Data Structure
===============================

The ``grove`` is a specialized B+ tree optimized for genomic interval storage and querying. It includes an embedded graph overlay that allows you to link keys within the grove, creating relationships between genomic features.

Key Types and the key_type_base Concept
----------------------------------------

The grove is highly flexible and can work with any key type that satisfies the ``key_type_base`` concept. Genogrove provides two built-in key types:

- ``interval`` - Basic genomic intervals (0-based, half-open)
- ``genomic_coordinate`` - Intervals with strand information

**Custom Key Types**

You can use any custom type as a key in the grove, as long as it satisfies the ``key_type_base`` concept requirements:

.. code-block:: cpp

   // Required operations for key_type_base concept:
   // 1. Comparison operators: <, >, ==
   // 2. Static overlap detection: overlap(a, b) -> bool
   // 3. Static aggregation: aggregate(vector<T>) -> T
   // 4. String representation: to_string() -> string

Example of a custom key type:

.. code-block:: cpp

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
       static bool overlap(const CustomInterval& a, const CustomInterval& b) {
           return !(a.end <= b.start || b.end <= a.start);
       }

       // Static aggregate method
       static CustomInterval aggregate(const std::vector<CustomInterval>& intervals) {
           if (intervals.empty()) return {0, 0, 0};
           size_t min_start = intervals[0].start;
           size_t max_end = intervals[0].end;
           for (const auto& iv : intervals) {
               min_start = std::min(min_start, iv.start);
               max_end = std::max(max_end, iv.end);
           }
           return {min_start, max_end, 0};
       }

       // String representation
       std::string to_string() const {
           return "[" + std::to_string(start) + ", " +
                  std::to_string(end) + ") p=" + std::to_string(priority);
       }
   };

   // Now you can use it with grove
   gst::grove<CustomInterval, std::string> my_grove(100);

Creating a Grove
----------------

Create a grove with specified template parameters and tree order:

.. code-block:: cpp

   #include <genogrove/structure/grove/grove.hpp>
   #include <genogrove/data_type/interval.hpp>

   namespace gdt = genogrove::data_type;
   namespace gst = genogrove::structure;

   int main() {
       // grove<key_type, data_type, edge_data_type>
       // Order determines max keys per node (higher = more cache-friendly)

       // Using built-in interval type
       gst::grove<gdt::interval, std::string> grove1(100);

       // Using genomic_coordinate (with strand)
       gst::grove<gdt::genomic_coordinate, std::string> grove2(100);

       // Using custom key type
       gst::grove<CustomInterval, std::string> grove3(100);

       return 0;
   }

**Template Parameters:**

- ``key_type``: Type satisfying ``key_type_base`` concept (interval, genomic_coordinate, or custom)
- ``data_type``: Associated data type (default: void for no data)
- ``edge_data_type``: Edge metadata for graph overlay (default: void)

Inserting Data
--------------

The grove supports multiple insertion modes with multi-index organization:

.. code-block:: cpp

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

**Insertion Modes:**

- ``unsorted`` (default): Full tree traversal for random data
- ``sorted``: Optimized O(1) insertion for pre-sorted data
- ``bulk``: Bulk insertion using hybrid bottom-up/append approach

**Multi-Index Organization:**

- Each index (e.g., chromosome) maintains a separate B+ tree
- Enables efficient chromosome-specific queries
- Automatic index creation on first insertion

Bulk Insertion
--------------

For loading large datasets efficiently, use bulk insertion. Bulk insertion uses a hybrid bottom-up/append approach that is significantly faster than incremental insertion.

**How It Works:**

- **Empty index**: Builds tree from bottom-up (O(n) time)

  - Creates fully-packed leaf nodes first
  - Then builds internal layers
  - ~10-20x faster than incremental insertion for large datasets
  - Better space utilization: 75-90% full nodes vs ~50% from split-based insertion

- **Existing data**: Appends to rightmost node

  - **CRITICAL PRECONDITION**: All new keys must be strictly greater than existing keys in the index
  - Throws ``std::runtime_error`` if precondition is violated

**Usage:**

.. code-block:: cpp

   #include <genogrove/structure/grove/grove.hpp>
   #include <genogrove/data_type/interval.hpp>
   #include <vector>

   namespace gdt = genogrove::data_type;
   namespace gst = genogrove::structure;

   int main() {
       gst::grove<gdt::interval, std::string> my_grove(100);

       // Prepare sorted data
       std::vector<gdt::interval> intervals = {
           {100, 200}, {300, 400}, {500, 600}
       };
       std::vector<std::string> names = {"gene1", "gene2", "gene3"};

       // Bulk insert with sorted data (fastest method)
       my_grove.insert_data("chr1", intervals, names, gst::sorted, gst::bulk);

       return 0;
   }

**Performance Comparison:**

For loading 1M intervals into an empty index:

- **Incremental insertion** (``unsorted``): ~10-20 seconds
- **Sorted insertion** (``sorted``): ~2-5 seconds
- **Bulk insertion** (``sorted, bulk``): ~0.5-1 second

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

Querying Intervals
------------------

Find all intervals that overlap with a query region:

.. code-block:: cpp

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

       // Query specific chromosome
       gdt::interval query{175, 225};
       auto results = my_grove.intersect(query, "chr1");

       // Process results
       for (auto* key : results.get_keys()) {
           std::cout << "Found: " << key->get_data()
                     << " at " << key->get_value().to_string() << "\n";
       }
       // Output: gene1, gene2 (gene3 doesn't overlap)

       // Query across all chromosomes
       auto all_results = my_grove.intersect(query);
       std::cout << "Total matches: " << all_results.get_keys().size() << "\n";

       return 0;
   }

**Query Features:**

- Efficient overlap-based searching using B+ tree structure
- Index-specific queries (single chromosome)
- Global queries (all chromosomes)
- Returns ``query_result`` containing matching keys

.. toctree::
   :maxdepth: 1

   graph

