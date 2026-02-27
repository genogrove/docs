# Graph Manipulation

Once you've built a graph by linking keys, GenoGrove provides a comprehensive set of functions to inspect, modify, and analyze the graph structure. This section covers operations for checking edge existence, retrieving edges, navigating neighbors, gathering statistics, and managing the graph lifecycle.

## Edge Inspection

### Checking if an edge exists (`has_edge`)

The `has_edge` function checks whether a directed edge exists from a source key to a target key.

**Function Signature:**

```cpp
bool has_edge(const key_type* source, const key_type* target) const
```

**Parameters:**

- `source` - Pointer to the source key
- `target` - Pointer to the target key

**Return Value:**

- Returns `true` if an edge exists from source to target, `false` otherwise

**Example:**

```cpp
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
```

**Use Cases:**

- Validating graph structure before analysis
- Preventing duplicate edge creation
- Conditional edge operations based on existing connections

### Retrieving edge metadata (`get_edges`)

The `get_edges` function retrieves the metadata for all outgoing edges from a source key. This is only available when the grove has a non-void `edge_data_type`. To get the target keys themselves, use `get_neighbors()` instead.

**Function Signature:**

```cpp
template<typename M = edge_data_type>
std::vector<M> get_edges(source) const
    requires (!std::is_void_v<edge_data_type>)
```

**Parameters:**

- `source` - Pointer to the source key

**Return Value:**

- Vector of edge metadata values (one per outgoing edge)

**Example:**

```cpp
gst::grove<gdt::interval, std::string, double> grove(100);

auto* enhancer = grove.insert_data("chr1", gdt::interval{1000, 1500}, "Enh1");
auto* gene1 = grove.insert_data("chr1", gdt::interval{5000, 10000}, "Gene1");
auto* gene2 = grove.insert_data("chr1", gdt::interval{15000, 20000}, "Gene2");

grove.add_edge(enhancer, gene1, 0.95);  // High confidence
grove.add_edge(enhancer, gene2, 0.65);  // Lower confidence

// Get metadata (confidence scores) for all edges from enhancer
auto scores = grove.get_edges(enhancer);

for (double confidence : scores) {
    std::cout << "Confidence: " << confidence << "\n";
}
```

To iterate over both targets and metadata together, use `get_edge_list()`:

```cpp
auto& edges = grove.get_edge_list(enhancer);

for (const auto& edge : edges) {
    std::cout << edge.target->get_data()
              << " (confidence: " << edge.metadata << ")\n";
}
```

**Use Cases:**

- Analyzing edge weights or metadata for downstream processing
- Aggregating metadata values (e.g., average confidence)
- Use `get_edge_list()` when you need both targets and metadata together

### Getting the edge list for a source (`get_edge_list`)

The `get_edge_list` function retrieves all outgoing edges from a source key as `edge` structs, each containing the target pointer and metadata (if any). Unlike `get_edges()` (metadata only) or `get_neighbors()` (targets only), this returns the full edge objects.

**Function Signature:**

```cpp
const std::vector<edge>& get_edge_list(source) const
```

**Parameters:**

- `source` - Pointer to the source key

**Return Value:**

- Const reference to vector of `edge` structs (each with `target` and `metadata` fields)
- Returns an empty vector if the source has no outgoing edges

**Example:**

```cpp
gst::grove<gdt::interval, std::string, double> grove(100);

auto* tf1 = grove.insert_data("chr1", gdt::interval{1000, 2000}, "TF1");
auto* gene1 = grove.insert_data("chr1", gdt::interval{5000, 6000}, "Gene1");
auto* gene2 = grove.insert_data("chr1", gdt::interval{7000, 8000}, "Gene2");

grove.add_edge(tf1, gene1, 0.9);
grove.add_edge(tf1, gene2, 0.7);

// Get all edges from tf1
const auto& edges = grove.get_edge_list(tf1);

std::cout << "TF1 targets (" << edges.size() << " edges):\n";
for (const auto& edge : edges) {
    std::cout << "  -> " << edge.target->get_data()
              << " (weight: " << edge.metadata << ")\n";
}
```

**Use Cases:**

- Accessing both target keys and metadata in a single iteration
- Efficient read-only access (returns a const reference, no copy)
- Building adjacency representations for graph algorithms

## Neighbor Queries

### Getting all neighbors (`get_neighbors`)

The `get_neighbors` function returns all target keys that are connected from a source key via outgoing edges.

**Function Signature:**

```cpp
std::vector<const key_type*> get_neighbors(const key_type* source) const
```

**Parameters:**

- `source` - Pointer to the source key

**Return Value:**

- Vector of pointers to neighbor keys (targets of outgoing edges)

**Example:**

```cpp
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
```

**Example: Path exploration**

```cpp
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
```

**Use Cases:**

- Graph traversal and path finding
- Analyzing connectivity patterns
- Building adjacency lists for graph algorithms

### Filtered neighbor queries (`get_neighbors_if`)

The `get_neighbors_if` function returns only neighbors whose edges satisfy a given predicate, allowing you to filter by edge metadata.

**Function Signature:**

```cpp
template<typename Predicate>
std::vector<const key_type*> get_neighbors_if(const key_type* source, Predicate pred) const
```

**Parameters:**

- `source` - Pointer to the source key
- `pred` - Predicate function that takes edge metadata and returns `bool`

**Return Value:**

- Vector of pointers to neighbor keys that pass the predicate filter

**Example: Confidence threshold**

```cpp
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
```

**Example: Distance-based filtering**

```cpp
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
```

**Use Cases:**

- Filtering by confidence scores or weights
- Distance-based queries in spatial networks
- Selecting edges by quality metrics

## Edge Modification

### Removing edges (`remove_edge`)

The `remove_edge` function removes a specific directed edge from the graph. The keys themselves remain in the grove.

**Function Signature:**

```cpp
bool remove_edge(source, target)
```

**Parameters:**

- `source` - Pointer to the source key
- `target` - Pointer to the target key

**Return Value:**

- Returns `true` if the edge was found and removed, `false` otherwise

**Example: Pruning low-quality edges**

```cpp
gst::grove<gdt::interval, std::string, double> grove(100);

auto* gene1 = grove.insert_data("chr1", gdt::interval{1000, 2000}, "GeneA");
auto* gene2 = grove.insert_data("chr1", gdt::interval{3000, 4000}, "GeneB");
auto* gene3 = grove.insert_data("chr1", gdt::interval{5000, 6000}, "GeneC");

grove.add_edge(gene1, gene2, 0.95);
grove.add_edge(gene1, gene3, 0.45);  // Low confidence

// Remove a specific edge
if (grove.remove_edge(gene1, gene3)) {
    std::cout << "Removed low-confidence edge to GeneC\n";
}
```

**Example: Updating graph structure**

```cpp
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
```

**Use Cases:**

- Pruning edges below quality thresholds
- Updating graph topology based on new evidence
- Removing erroneous connections

## Graph Statistics

### Counting outgoing edges (`out_degree`)

The `out_degree` function returns the number of outgoing edges from a specific key.

**Function Signature:**

```cpp
size_t out_degree(const key_type* source) const
```

**Parameters:**

- `source` - Pointer to the source key

**Return Value:**

- Number of outgoing edges from the source key

**Example:**

```cpp
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
```

**Example: Finding hub genes**

```cpp
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
```

**Use Cases:**

- Identifying hub nodes in networks
- Analyzing node importance by connectivity
- Filtering nodes by degree thresholds

### Total edge count (`edge_count`)

The `edge_count` function returns the total number of edges in the entire graph.

**Function Signature:**

```cpp
size_t edge_count() const
```

**Return Value:**

- Total number of directed edges in the graph

**Example:**

```cpp
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
```

**Use Cases:**

- Computing graph density
- Tracking graph size during construction
- Validating graph operations

### Counting vertices (`vertex_count`, `indexed_vertex_count`, `external_vertex_count`)

These functions count vertices (keys) in the grove.

**Function Signatures:**

```cpp
size_t vertex_count() const              // Total keys in the grove (indexed + external)
size_t indexed_vertex_count() const      // Keys stored in B+ tree (findable via spatial queries)
size_t external_vertex_count() const     // Graph-only keys (not indexed, not findable via spatial queries)
size_t vertex_count_with_edges() const   // Keys with at least one outgoing edge
```

**Return Value:**

- `vertex_count()`: Total number of keys in the grove, including isolated vertices with no edges
- `indexed_vertex_count()`: Number of keys indexed in the B+ tree (can be found via `intersect`)
- `external_vertex_count()`: Number of keys that participate in graph edges but are not indexed
- `vertex_count_with_edges()`: Number of keys that have at least one outgoing edge

**Example:**

```cpp
gst::grove<gdt::interval, std::string, void> grove(100);

auto* k1 = grove.insert_data("chr1", gdt::interval{100, 200}, "A");
auto* k2 = grove.insert_data("chr1", gdt::interval{300, 400}, "B");
auto* k3 = grove.insert_data("chr1", gdt::interval{500, 600}, "C");
auto* k4 = grove.insert_data("chr1", gdt::interval{700, 800}, "D");

grove.add_edge(k1, k2);
grove.add_edge(k2, k3);
// k1 -> k2 -> k3, k4 is isolated

std::cout << "Total vertices: " << grove.vertex_count() << "\n";
// Output: 4 (all keys, including isolated k4)

std::cout << "Indexed vertices: " << grove.indexed_vertex_count() << "\n";
// Output: 4 (all keys are in the B+ tree)

std::cout << "External vertices: " << grove.external_vertex_count() << "\n";
// Output: 0 (no graph-only keys)

std::cout << "Keys with outgoing edges: " << grove.vertex_count_with_edges() << "\n";
// Output: 2 (k1 and k2 have outgoing edges; k3 only receives)
```

**Example: Graph density calculation**

```cpp
gst::grove<gdt::interval, std::string, void> grove(100);

// Build graph...

size_t vertices = grove.vertex_count();
size_t edges = grove.edge_count();

double max_edges = vertices * (vertices - 1);  // For directed graph
double density = (max_edges > 0) ? (edges / max_edges) : 0.0;

std::cout << "Graph density: " << density << "\n";
```

**Use Cases:**

- Computing graph statistics (density, average degree)
- Distinguishing indexed vs. external (graph-only) keys
- Identifying isolated vs. connected components
- Validating graph construction

## Graph Management

### Clearing the graph (`clear_graph`)

The `clear_graph` function removes all edges from the graph while keeping all keys in the grove.

**Function Signature:**

```cpp
void clear_graph()
```

**Return Value:**

- Returns `void` (no return value)
- All edges are removed; keys remain in the grove with their spatial indices intact

**Example:**

```cpp
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
std::cout << "Keys still exist: " << results.get_keys().size() << "\n";
// Output: Keys still exist: 1
```

**Example: Rebuilding graph with different criteria**

```cpp
gst::grove<gdt::interval, std::string, double> grove(100);

// Insert features
auto keys = grove.insert_data("chr1", data, gst::sorted, gst::bulk);

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
```

**Use Cases:**

- Rebuilding graph with different parameters
- Resetting graph state while preserving spatial data
- Separating graph construction from spatial indexing

### Checking if graph is empty (`graph_empty`)

The `graph_empty` function checks whether the graph contains any edges.

**Function Signature:**

```cpp
bool graph_empty() const
```

**Return Value:**

- Returns `true` if the graph has no edges, `false` otherwise

**Example:**

```cpp
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
```

**Example: Conditional graph operations**

```cpp
gst::grove<gdt::interval, std::string, double> grove(100);

// Load data...
auto keys = grove.insert_data("chr1", data, gst::sorted, gst::bulk);

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
```

**Use Cases:**

- Validating graph state before operations
- Conditional graph building
- Lazy graph initialization
