Graph Manipulation
===================

Once you've built a graph by linking keys, GenoGrove provides a comprehensive set of functions to inspect, modify, and analyze the graph structure. This section covers operations for checking edge existence, retrieving edges, navigating neighbors, gathering statistics, and managing the graph lifecycle.

Edge Inspection
^^^^^^^^^^^^^^^

Checking if an edge exists (``has_edge``)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``has_edge`` function checks whether a directed edge exists from a source key to a target key.

**Function Signature:**

.. code-block:: cpp

   bool has_edge(const key_type* source, const key_type* target) const

**Parameters:**

- ``source`` - Pointer to the source key
- ``target`` - Pointer to the target key

**Return Value:**

- Returns ``true`` if an edge exists from source to target, ``false`` otherwise

**Example:**

.. code-block:: cpp

   gst::grove<gdt::interval, std::string, double> grove(100);

   auto* exon1 = grove.insert_data("chr1", gdt::interval{100, 200}, "exon1");
   auto* exon2 = grove.insert_data("chr1", gdt::interval{300, 400}, "exon2");
   auto* exon3 = grove.insert_data("chr1", gdt::interval{500, 600}, "exon3");

   grove.add_edge(exon1, exon2, 0.95);

   // Check edge existence
   if (grove.has_edge(exon1, exon2)) {
       std::cout << "Edge exists from exon1 to exon2\n";
   }

   if (!grove.has_edge(exon1, exon3)) {
       std::cout << "No direct edge from exon1 to exon3\n";
   }

**Use Cases:**

- Validating graph structure before analysis
- Preventing duplicate edge creation
- Conditional edge operations based on existing connections

Retrieving edge information (``get_edges``)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``get_edges`` function retrieves all outgoing edges from a source key, including their metadata (if present).

**Function Signature:**

.. code-block:: cpp

   // Without metadata (returns vector of target pointers)
   std::vector<const key_type*> get_edges(const key_type* source) const

   // With metadata (returns vector of pairs: target pointer and metadata)
   std::vector<std::pair<const key_type*, EdgeMetadata>> get_edges(const key_type* source) const

**Parameters:**

- ``source`` - Pointer to the source key

**Return Value:**

- **Without metadata**: Vector of pointers to target keys
- **With metadata**: Vector of pairs containing target key pointers and their associated metadata

**Example without metadata:**

.. code-block:: cpp

   gst::grove<gdt::interval, std::string, void> grove(100);

   auto* gene1 = grove.insert_data("chr1", gdt::interval{1000, 2000}, "GeneA");
   auto* gene2 = grove.insert_data("chr1", gdt::interval{3000, 4000}, "GeneB");
   auto* gene3 = grove.insert_data("chr1", gdt::interval{5000, 6000}, "GeneC");

   grove.add_edge(gene1, gene2);
   grove.add_edge(gene1, gene3);

   // Get all outgoing edges from gene1
   auto edges = grove.get_edges(gene1);

   std::cout << "GeneA connects to " << edges.size() << " genes:\n";
   for (auto* target : edges) {
       std::cout << "  -> " << target->get_data() << "\n";
   }

**Example with metadata:**

.. code-block:: cpp

   gst::grove<gdt::interval, std::string, double> grove(100);

   auto* enhancer = grove.insert_data("chr1", gdt::interval{1000, 1500}, "Enh1");
   auto* gene1 = grove.insert_data("chr1", gdt::interval{5000, 10000}, "Gene1");
   auto* gene2 = grove.insert_data("chr1", gdt::interval{15000, 20000}, "Gene2");

   grove.add_edge(enhancer, gene1, 0.95);  // High confidence
   grove.add_edge(enhancer, gene2, 0.65);  // Lower confidence

   // Get edges with confidence scores
   auto edges = grove.get_edges(enhancer);

   std::cout << "Enhancer interactions:\n";
   for (const auto& [target, confidence] : edges) {
       std::cout << "  -> " << target->get_data()
                 << " (confidence: " << confidence << ")\n";
   }

   // Filter by confidence threshold
   std::cout << "\nHigh-confidence interactions (>0.8):\n";
   for (const auto& [target, confidence] : edges) {
       if (confidence > 0.8) {
           std::cout << "  -> " << target->get_data() << "\n";
       }
   }

**Use Cases:**

- Analyzing edge weights or metadata for downstream processing
- Filtering edges based on metadata criteria
- Exporting graph structure with attributes

Getting the full edge list (``get_edge_list``)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``get_edge_list`` function retrieves all edges in the entire graph, not just from a single source key.

**Function Signature:**

.. code-block:: cpp

   // Without metadata
   std::vector<std::pair<const key_type*, const key_type*>> get_edge_list() const

   // With metadata
   std::vector<std::tuple<const key_type*, const key_type*, EdgeMetadata>> get_edge_list() const

**Return Value:**

- **Without metadata**: Vector of pairs (source, target)
- **With metadata**: Vector of tuples (source, target, metadata)

**Example:**

.. code-block:: cpp

   gst::grove<gdt::interval, std::string, double> grove(100);

   // Build a small regulatory network
   auto* tf1 = grove.insert_data("chr1", gdt::interval{1000, 2000}, "TF1");
   auto* tf2 = grove.insert_data("chr1", gdt::interval{3000, 4000}, "TF2");
   auto* gene1 = grove.insert_data("chr1", gdt::interval{5000, 6000}, "Gene1");
   auto* gene2 = grove.insert_data("chr1", gdt::interval{7000, 8000}, "Gene2");

   grove.add_edge(tf1, gene1, 0.9);
   grove.add_edge(tf1, gene2, 0.7);
   grove.add_edge(tf2, gene1, 0.8);

   // Get all edges in the graph
   auto all_edges = grove.get_edge_list();

   std::cout << "Complete regulatory network (" << all_edges.size() << " edges):\n";
   for (const auto& [source, target, weight] : all_edges) {
       std::cout << source->get_data() << " -> " << target->get_data()
                 << " (weight: " << weight << ")\n";
   }

**Example: Exporting to edge list format**

.. code-block:: cpp

   gst::grove<gdt::interval, std::string, double> grove(100);

   // ... build graph ...

   // Export to CSV format
   std::ofstream out("network.csv");
   out << "source,target,weight\n";

   auto edges = grove.get_edge_list();
   for (const auto& [source, target, weight] : edges) {
       out << source->get_data() << ","
           << target->get_data() << ","
           << weight << "\n";
   }

**Use Cases:**

- Exporting entire graph to external formats (GraphML, CSV, JSON)
- Computing global graph properties (density, clustering coefficient)
- Serializing graph structure for storage or transmission

Neighbor Queries
^^^^^^^^^^^^^^^^

Getting all neighbors (``get_neighbors``)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``get_neighbors`` function returns all target keys that are connected from a source key via outgoing edges.

**Function Signature:**

.. code-block:: cpp

   std::vector<const key_type*> get_neighbors(const key_type* source) const

**Parameters:**

- ``source`` - Pointer to the source key

**Return Value:**

- Vector of pointers to neighbor keys (targets of outgoing edges)

**Example:**

.. code-block:: cpp

   gst::grove<gdt::interval, std::string, void> grove(100);

   auto* exon1 = grove.insert_data("chr1", gdt::interval{100, 200}, "exon1");
   auto* exon2a = grove.insert_data("chr1", gdt::interval{300, 400}, "exon2a");
   auto* exon2b = grove.insert_data("chr1", gdt::interval{350, 450}, "exon2b");
   auto* exon3 = grove.insert_data("chr1", gdt::interval{500, 600}, "exon3");

   // Alternative splicing: exon1 can splice to either exon2a or exon2b
   grove.add_edge(exon1, exon2a);
   grove.add_edge(exon1, exon2b);
   grove.add_edge(exon2a, exon3);
   grove.add_edge(exon2b, exon3);

   // Find all possible next exons after exon1
   auto next_exons = grove.get_neighbors(exon1);

   std::cout << "Exon1 can splice to " << next_exons.size() << " exons:\n";
   for (auto* exon : next_exons) {
       std::cout << "  -> " << exon->get_data() << "\n";
   }

**Example: Path exploration**

.. code-block:: cpp

   gst::grove<gdt::interval, std::string, void> pathway(100);

   // Build metabolic pathway
   auto* glucose = pathway.insert_data("chr1", gdt::interval{1, 100}, "Glucose");
   auto* g6p = pathway.insert_data("chr1", gdt::interval{101, 200}, "G6P");
   auto* f6p = pathway.insert_data("chr1", gdt::interval{201, 300}, "F6P");

   pathway.add_edge(glucose, g6p);
   pathway.add_edge(g6p, f6p);

   // Trace pathway forward from glucose
   auto* current = glucose;
   std::cout << "Pathway: " << current->get_data();

   while (true) {
       auto neighbors = pathway.get_neighbors(current);
       if (neighbors.empty()) break;

       current = neighbors[0];  // Follow first path
       std::cout << " -> " << current->get_data();
   }
   std::cout << "\n";

**Use Cases:**

- Graph traversal and path finding
- Analyzing connectivity patterns
- Building adjacency lists for graph algorithms

Filtered neighbor queries (``get_neighbors_if``)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``get_neighbors_if`` function returns only neighbors whose edges satisfy a given predicate, allowing you to filter by edge metadata.

**Function Signature:**

.. code-block:: cpp

   template<typename Predicate>
   std::vector<const key_type*> get_neighbors_if(const key_type* source, Predicate pred) const

**Parameters:**

- ``source`` - Pointer to the source key
- ``pred`` - Predicate function that takes edge metadata and returns ``bool``

**Return Value:**

- Vector of pointers to neighbor keys that pass the predicate filter

**Example: Confidence threshold**

.. code-block:: cpp

   gst::grove<gdt::interval, std::string, double> grove(100);

   auto* enhancer = grove.insert_data("chr1", gdt::interval{1000, 1500}, "Enh1");
   auto* gene1 = grove.insert_data("chr1", gdt::interval{5000, 10000}, "Gene1");
   auto* gene2 = grove.insert_data("chr1", gdt::interval{15000, 20000}, "Gene2");
   auto* gene3 = grove.insert_data("chr1", gdt::interval{25000, 30000}, "Gene3");

   grove.add_edge(enhancer, gene1, 0.95);  // High confidence
   grove.add_edge(enhancer, gene2, 0.65);  // Medium confidence
   grove.add_edge(enhancer, gene3, 0.45);  // Low confidence

   // Get only high-confidence targets (>0.8)
   auto high_conf = grove.get_neighbors_if(enhancer,
       [](double confidence) { return confidence > 0.8; });

   std::cout << "High-confidence targets: " << high_conf.size() << "\n";
   for (auto* target : high_conf) {
       std::cout << "  -> " << target->get_data() << "\n";
   }

**Example: Distance-based filtering**

.. code-block:: cpp

   gst::grove<gdt::interval, std::string, size_t> grove(100);

   // Edges store genomic distance
   auto* gene1 = grove.insert_data("chr1", gdt::interval{1000, 2000}, "GeneA");
   auto* gene2 = grove.insert_data("chr1", gdt::interval{10000, 11000}, "GeneB");
   auto* gene3 = grove.insert_data("chr1", gdt::interval{50000, 51000}, "GeneC");

   grove.add_edge(gene1, gene2, 8000);   // 8kb apart
   grove.add_edge(gene1, gene3, 48000);  // 48kb apart

   // Find genes within 10kb
   auto nearby = grove.get_neighbors_if(gene1,
       [](size_t distance) { return distance <= 10000; });

   std::cout << "Nearby genes (<10kb): " << nearby.size() << "\n";

**Use Cases:**

- Filtering by confidence scores or weights
- Distance-based queries in spatial networks
- Selecting edges by quality metrics

Edge Modification
^^^^^^^^^^^^^^^^^

Removing edges (``remove_edge``)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``remove_edge`` function removes a specific directed edge from the graph. The keys themselves remain in the grove.

**Function Signature:**

.. code-block:: cpp

   void remove_edge(const key_type* source, const key_type* target)

**Parameters:**

- ``source`` - Pointer to the source key
- ``target`` - Pointer to the target key

**Return Value:**

- Returns ``void`` (no return value)
- If the edge doesn't exist, the operation has no effect

**Example: Pruning low-quality edges**

.. code-block:: cpp

   gst::grove<gdt::interval, std::string, double> grove(100);

   auto* gene1 = grove.insert_data("chr1", gdt::interval{1000, 2000}, "GeneA");
   auto* gene2 = grove.insert_data("chr1", gdt::interval{3000, 4000}, "GeneB");
   auto* gene3 = grove.insert_data("chr1", gdt::interval{5000, 6000}, "GeneC");

   grove.add_edge(gene1, gene2, 0.95);
   grove.add_edge(gene1, gene3, 0.45);  // Low confidence

   // Get edges and remove low-confidence ones
   auto edges = grove.get_edges(gene1);
   for (const auto& [target, confidence] : edges) {
       if (confidence < 0.5) {
           std::cout << "Removing low-confidence edge to " << target->get_data() << "\n";
           grove.remove_edge(gene1, target);
       }
   }

**Example: Updating graph structure**

.. code-block:: cpp

   gst::grove<gdt::interval, std::string, void> grove(100);

   auto* exon1 = grove.insert_data("chr1", gdt::interval{100, 200}, "exon1");
   auto* exon2 = grove.insert_data("chr1", gdt::interval{300, 400}, "exon2");
   auto* exon3 = grove.insert_data("chr1", gdt::interval{500, 600}, "exon3");

   // Initial structure: exon1 -> exon2 -> exon3
   grove.add_edge(exon1, exon2);
   grove.add_edge(exon2, exon3);

   // Discover that exon1 actually connects directly to exon3 (exon skipping)
   grove.add_edge(exon1, exon3);

   // Optionally remove the intermediate connection
   grove.remove_edge(exon1, exon2);

   // Now: exon1 -> exon3, exon2 -> exon3

**Use Cases:**

- Pruning edges below quality thresholds
- Updating graph topology based on new evidence
- Removing erroneous connections

Graph Statistics
^^^^^^^^^^^^^^^^

Counting outgoing edges (``out_degree``)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``out_degree`` function returns the number of outgoing edges from a specific key.

**Function Signature:**

.. code-block:: cpp

   size_t out_degree(const key_type* source) const

**Parameters:**

- ``source`` - Pointer to the source key

**Return Value:**

- Number of outgoing edges from the source key

**Example:**

.. code-block:: cpp

   gst::grove<gdt::interval, std::string, void> grove(100);

   auto* tf = grove.insert_data("chr1", gdt::interval{1000, 2000}, "TF1");
   auto* gene1 = grove.insert_data("chr1", gdt::interval{3000, 4000}, "Gene1");
   auto* gene2 = grove.insert_data("chr1", gdt::interval{5000, 6000}, "Gene2");
   auto* gene3 = grove.insert_data("chr1", gdt::interval{7000, 8000}, "Gene3");

   grove.add_edge(tf, gene1);
   grove.add_edge(tf, gene2);
   grove.add_edge(tf, gene3);

   std::cout << "TF1 regulates " << grove.out_degree(tf) << " genes\n";
   // Output: TF1 regulates 3 genes

**Example: Finding hub genes**

.. code-block:: cpp

   gst::grove<gdt::interval, std::string, void> network(100);

   // Build gene regulatory network...
   std::vector<const key_type*> all_genes = { /* ... */ };

   // Find genes with high out-degree (hub regulators)
   std::vector<const key_type*> hubs;
   for (auto* gene : all_genes) {
       if (network.out_degree(gene) >= 10) {
           hubs.push_back(gene);
           std::cout << "Hub gene: " << gene->get_data()
                     << " (regulates " << network.out_degree(gene) << " targets)\n";
       }
   }

**Use Cases:**

- Identifying hub nodes in networks
- Analyzing node importance by connectivity
- Filtering nodes by degree thresholds

Total edge count (``edge_count``)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``edge_count`` function returns the total number of edges in the entire graph.

**Function Signature:**

.. code-block:: cpp

   size_t edge_count() const

**Return Value:**

- Total number of directed edges in the graph

**Example:**

.. code-block:: cpp

   gst::grove<gdt::interval, std::string, void> grove(100);

   // Build graph...
   auto* k1 = grove.insert_data("chr1", gdt::interval{100, 200}, "A");
   auto* k2 = grove.insert_data("chr1", gdt::interval{300, 400}, "B");
   auto* k3 = grove.insert_data("chr1", gdt::interval{500, 600}, "C");

   grove.add_edge(k1, k2);
   grove.add_edge(k2, k3);
   grove.add_edge(k1, k3);

   std::cout << "Graph has " << grove.edge_count() << " edges\n";
   // Output: Graph has 3 edges

**Use Cases:**

- Computing graph density
- Tracking graph size during construction
- Validating graph operations

Counting vertices (``vertex_count`` and ``vertex_count_with_edges``)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

These functions count vertices (keys) that participate in the graph structure.

**Function Signatures:**

.. code-block:: cpp

   size_t vertex_count() const                    // Keys with at least one edge (in or out)
   size_t vertex_count_with_edges() const         // Keys with at least one outgoing edge

**Return Value:**

- ``vertex_count()``: Number of keys that have at least one incoming or outgoing edge
- ``vertex_count_with_edges()``: Number of keys that have at least one outgoing edge

**Example:**

.. code-block:: cpp

   gst::grove<gdt::interval, std::string, void> grove(100);

   auto* k1 = grove.insert_data("chr1", gdt::interval{100, 200}, "A");
   auto* k2 = grove.insert_data("chr1", gdt::interval{300, 400}, "B");
   auto* k3 = grove.insert_data("chr1", gdt::interval{500, 600}, "C");
   auto* k4 = grove.insert_data("chr1", gdt::interval{700, 800}, "D");

   grove.add_edge(k1, k2);
   grove.add_edge(k2, k3);
   // k1 -> k2 -> k3, k4 is isolated

   std::cout << "Keys with edges: " << grove.vertex_count() << "\n";
   // Output: 3 (k1, k2, k3 participate in edges)

   std::cout << "Keys with outgoing edges: " << grove.vertex_count_with_edges() << "\n";
   // Output: 2 (k1 and k2 have outgoing edges; k3 only receives)

**Example: Graph density calculation**

.. code-block:: cpp

   gst::grove<gdt::interval, std::string, void> grove(100);

   // Build graph...

   size_t vertices = grove.vertex_count();
   size_t edges = grove.edge_count();

   double max_edges = vertices * (vertices - 1);  // For directed graph
   double density = (max_edges > 0) ? (edges / max_edges) : 0.0;

   std::cout << "Graph density: " << density << "\n";

**Use Cases:**

- Computing graph statistics (density, average degree)
- Identifying isolated vs. connected components
- Validating graph construction

Graph Management
^^^^^^^^^^^^^^^^

Clearing the graph (``clear_graph``)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``clear_graph`` function removes all edges from the graph while keeping all keys in the grove.

**Function Signature:**

.. code-block:: cpp

   void clear_graph()

**Return Value:**

- Returns ``void`` (no return value)
- All edges are removed; keys remain in the grove with their spatial indices intact

**Example:**

.. code-block:: cpp

   gst::grove<gdt::interval, std::string, double> grove(100);

   // Build graph
   auto* k1 = grove.insert_data("chr1", gdt::interval{100, 200}, "A");
   auto* k2 = grove.insert_data("chr1", gdt::interval{300, 400}, "B");
   grove.add_edge(k1, k2, 0.9);

   std::cout << "Before: " << grove.edge_count() << " edges\n";
   // Output: Before: 1 edges

   // Clear all edges
   grove.clear_graph();

   std::cout << "After: " << grove.edge_count() << " edges\n";
   // Output: After: 0 edges

   // Keys still exist and can be queried
   auto results = grove.intersect(gdt::interval{50, 150}, "chr1");
   std::cout << "Keys still exist: " << results.size() << "\n";
   // Output: Keys still exist: 1

**Example: Rebuilding graph with different criteria**

.. code-block:: cpp

   gst::grove<gdt::interval, std::string, double> grove(100);

   // Insert features
   auto keys = grove.insert_data_bulk("chr1", intervals, names);

   // Build initial graph with permissive threshold
   for (size_t i = 0; i < keys.size() - 1; ++i) {
       double score = calculate_score(keys[i], keys[i+1]);
       if (score > 0.5) {
           grove.add_edge(keys[i], keys[i+1], score);
       }
   }

   std::cout << "Initial graph: " << grove.edge_count() << " edges\n";

   // Rebuild with stricter threshold
   grove.clear_graph();

   for (size_t i = 0; i < keys.size() - 1; ++i) {
       double score = calculate_score(keys[i], keys[i+1]);
       if (score > 0.8) {  // Stricter threshold
           grove.add_edge(keys[i], keys[i+1], score);
       }
   }

   std::cout << "Rebuilt graph: " << grove.edge_count() << " edges\n";

**Use Cases:**

- Rebuilding graph with different parameters
- Resetting graph state while preserving spatial data
- Separating graph construction from spatial indexing

Checking if graph is empty (``graph_empty``)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``graph_empty`` function checks whether the graph contains any edges.

**Function Signature:**

.. code-block:: cpp

   bool graph_empty() const

**Return Value:**

- Returns ``true`` if the graph has no edges, ``false`` otherwise

**Example:**

.. code-block:: cpp

   gst::grove<gdt::interval, std::string, void> grove(100);

   // Insert keys but no edges yet
   auto* k1 = grove.insert_data("chr1", gdt::interval{100, 200}, "A");
   auto* k2 = grove.insert_data("chr1", gdt::interval{300, 400}, "B");

   if (grove.graph_empty()) {
       std::cout << "Graph is empty, building connections...\n";
       grove.add_edge(k1, k2);
   }

   if (!grove.graph_empty()) {
       std::cout << "Graph now contains " << grove.edge_count() << " edges\n";
   }

**Example: Conditional graph operations**

.. code-block:: cpp

   gst::grove<gdt::interval, std::string, double> grove(100);

   // Load data...
   auto keys = grove.insert_data_bulk("chr1", intervals, names);

   // Only build graph if not already built
   if (grove.graph_empty()) {
       std::cout << "Building graph from " << keys.size() << " features...\n";

       grove.link_if(keys, [](auto* k1, auto* k2) -> std::optional<double> {
           // Link adjacent features with distance as weight
           size_t distance = k2->get_value().get_start() - k1->get_value().get_end();
           if (distance < 10000) {
               return static_cast<double>(distance);
           }
           return std::nullopt;
       });

       std::cout << "Built graph with " << grove.edge_count() << " edges\n";
   } else {
       std::cout << "Graph already exists with " << grove.edge_count() << " edges\n";
   }

**Use Cases:**

- Validating graph state before operations
- Conditional graph building
- Lazy graph initialization