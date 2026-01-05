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
- ``bulk``: Bulk insertion (not fully implemented)

**Multi-Index Organization:**

- Each index (e.g., chromosome) maintains a separate B+ tree
- Enables efficient chromosome-specific queries
- Automatic index creation on first insertion

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

Graph Overlay: Linking Keys Within the Grove
=============================================

The grove includes an embedded graph overlay that allows you to create directed edges between keys stored in the tree. This is useful for representing relationships between genomic features, such as:

- Transcript structures (linking exons)
- Gene regulatory networks
- Protein-protein interaction networks
- Any relationship between genomic regions

Building Graphs by Linking Keys
--------------------------------

Create directed edges between keys within your grove:

.. code-block:: cpp

   #include <genogrove/structure/grove/grove.hpp>
   #include <genogrove/data_type/interval.hpp>

   namespace gdt = genogrove::data_type;
   namespace gst = genogrove::structure;

   int main() {
       // Create grove with edge metadata (e.g., confidence scores)
       gst::grove<gdt::interval, std::string, double> my_grove(100);

       // Insert features and store pointers to keys
       auto* exon1 = my_grove.insert_data("chr1", gdt::interval{100, 200}, "exon1");
       auto* exon2 = my_grove.insert_data("chr1", gdt::interval{300, 400}, "exon2");
       auto* exon3 = my_grove.insert_data("chr1", gdt::interval{500, 600}, "exon3");

       // Link keys with edges (transcript structure)
       my_grove.add_edge(exon1, exon2, 0.95);  // edge weight/confidence
       my_grove.add_edge(exon2, exon3, 0.98);

       // Alternative splicing - create another path
       auto* exon2b = my_grove.insert_data("chr1", gdt::interval{350, 450}, "exon2b");
       my_grove.add_edge(exon1, exon2b, 0.75);
       my_grove.add_edge(exon2b, exon3, 0.80);

       return 0;
   }

**Key Points:**

- Edges are directed (source → target)
- Edges can have optional metadata (third template parameter)
- Keys from different indices (chromosomes) can be linked
- The graph overlay shares the grove's lifetime

Navigating the Graph
--------------------

Query and navigate relationships between keys:

.. code-block:: cpp

   #include <genogrove/structure/grove/grove.hpp>
   #include <genogrove/data_type/interval.hpp>

   namespace gdt = genogrove::data_type;
   namespace gst = genogrove::structure;

   int main() {
       gst::grove<gdt::interval, std::string, double> my_grove(100);

       auto* exon1 = my_grove.insert_data("chr1", gdt::interval{100, 200}, "exon1");
       auto* exon2 = my_grove.insert_data("chr1", gdt::interval{300, 400}, "exon2");
       auto* exon3 = my_grove.insert_data("chr1", gdt::interval{500, 600}, "exon3");

       my_grove.add_edge(exon1, exon2, 0.95);
       my_grove.add_edge(exon2, exon3, 0.60);

       // Get all neighbors (targets of outgoing edges)
       auto neighbors = my_grove.get_neighbors(exon1);
       for (auto* neighbor : neighbors) {
           std::cout << "Connected to: " << neighbor->get_data() << "\n";
       }

       // Get filtered neighbors (e.g., high confidence edges only)
       auto high_conf = my_grove.get_neighbors_if(exon1,
           [](double weight) { return weight > 0.9; });

       // Check if specific edge exists
       if (my_grove.has_edge(exon1, exon2)) {
           std::cout << "Direct connection exists\n";
       }

       // Get graph statistics
       std::cout << "Out-degree of exon1: " << my_grove.out_degree(exon1) << "\n";
       std::cout << "Total edges in graph: " << my_grove.edge_count() << "\n";
       std::cout << "Vertices with edges: " << my_grove.vertex_count() << "\n";

       // Remove an edge
       my_grove.remove_edge(exon2, exon3);

       // Clear all edges (keeps keys in grove)
       my_grove.clear_graph();

       return 0;
   }

**Graph Methods:**

- ``add_edge(source, target)`` - Create edge without metadata
- ``add_edge(source, target, metadata)`` - Create edge with metadata
- ``remove_edge(source, target)`` - Remove specific edge
- ``get_neighbors(source)`` - Get all targets of outgoing edges
- ``get_neighbors_if(source, predicate)`` - Get filtered neighbors
- ``has_edge(source, target)`` - Check if edge exists
- ``out_degree(source)`` - Count outgoing edges from a key
- ``edge_count()`` - Total edges in the graph
- ``vertex_count()`` - Number of keys with at least one edge
- ``clear_graph()`` - Remove all edges (keeps keys in grove)

Graph Overlay Without Metadata
-------------------------------

If you don't need edge metadata, use ``void`` as the third template parameter:

.. code-block:: cpp

   // No edge metadata
   gst::grove<gdt::interval, std::string, void> my_grove(100);

   auto* key1 = my_grove.insert_data("chr1", gdt::interval{100, 200}, "feature1");
   auto* key2 = my_grove.insert_data("chr1", gdt::interval{300, 400}, "feature2");

   // Add edge without metadata
   my_grove.add_edge(key1, key2);

   // Navigate normally
   auto neighbors = my_grove.get_neighbors(key1);

Using Different Key Types with Graph Overlay
---------------------------------------------

The graph overlay works with any key type, including custom types:

.. code-block:: cpp

   // Using genomic_coordinate (with strand)
   gst::grove<gdt::genomic_coordinate, std::string> stranded_grove(100);

   auto* fwd_feature = stranded_grove.insert_data(
       "chr1",
       gdt::genomic_coordinate{'+', 100, 200},
       "forward_gene"
   );

   auto* rev_feature = stranded_grove.insert_data(
       "chr1",
       gdt::genomic_coordinate{'-', 300, 400},
       "reverse_gene"
   );

   // Link features on opposite strands
   stranded_grove.add_edge(fwd_feature, rev_feature);

   // Or with custom key types
   gst::grove<CustomInterval, std::string> custom_grove(100);
   // Works the same way!

Combining Interval Queries with Graph Navigation
-------------------------------------------------

A powerful pattern: query for intervals, then navigate their relationships:

.. code-block:: cpp

   gst::grove<gdt::interval, std::string, double> my_grove(100);

   // Insert and link features
   auto* gene1 = my_grove.insert_data("chr1", gdt::interval{1000, 2000}, "GeneA");
   auto* gene2 = my_grove.insert_data("chr1", gdt::interval{3000, 4000}, "GeneB");
   auto* gene3 = my_grove.insert_data("chr1", gdt::interval{5000, 6000}, "GeneC");

   my_grove.add_edge(gene1, gene2, 0.9);  // GeneA regulates GeneB
   my_grove.add_edge(gene1, gene3, 0.8);  // GeneA regulates GeneC

   // Query for genes in a region
   gdt::interval query{900, 2500};
   auto results = my_grove.intersect(query, "chr1");

   // For each overlapping gene, find what it regulates
   for (auto* key : results.get_keys()) {
       std::cout << key->get_data() << " regulates:\n";
       auto targets = my_grove.get_neighbors(key);
       for (auto* target : targets) {
           std::cout << "  -> " << target->get_data() << "\n";
       }
   }