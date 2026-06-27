# Linking Keys

The grove includes an (optional) embedded graph overlay that allows you to create directed edges between keys
stored in the tree. This can be useful for representing relationships between genomic features, such as
transcript structures, gene regulatory networks or any relationship between genomic regions.

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

The graph overlay is an integral part of the grove structure and shares its lifetime. When creating a grove, you
specify whether edges will carry metadata through the grove's third template parameter. This design decision must
be made upfront as it determines the grove's type.

You can create edges in two ways:

1. **Without metadata** - Simple directed connections between keys
2. **With metadata** - Edges carry additional information (e.g., confidence scores, weights, relationship types)

**Grove Setup:**

```cpp
// If you don't need edges at all, omit the third parameter entirely
gst::grove<gdt::interval, std::string> simple_grove(100);

// Grove without edge metadata (use void as third parameter)
gst::grove<gdt::interval, std::string, void> grove_no_metadata(100);

// Grove with edge metadata (third parameter specifies the metadata type)
gst::grove<gdt::interval, std::string, double> grove_with_metadata(100);
```

### Adding an Edge (`add_edge`)

The `add_edge` function creates a directed connection from one key to another in the grove's graph overlay.

**Function Signature:**

```cpp
// Without metadata
void add_edge(gdt::key<key_type, data_type>* source, gdt::key<key_type, data_type>* target)

// With metadata
void add_edge(gdt::key<key_type, data_type>* source, gdt::key<key_type, data_type>* target,
              EdgeMetadata&& metadata)
```

**Parameters:**

- `source` - Pointer to the source key (obtained from insert operations or queries)
- `target` - Pointer to the target key (where the edge points to)
- `metadata` - Optional edge metadata (e.g., confidence score, weight, relationship type)

**Return Value:**

- Returns `void` (no return value)
- The edge is created and stored internally in the graph overlay

**Requirements:**

- Both source and target pointers must be valid keys in the grove
- The pointers should come from `insert_data` calls on the same grove instance
- If an edge already exists between the same source and target, the behavior depends on the implementation

**Example:**

```cpp
auto* key1 = my_grove.insert_data("chr1", gdt::interval{100, 200}, "exon1");
auto* key2 = my_grove.insert_data("chr1", gdt::interval{300, 400}, "exon2");

// Create edge with metadata (confidence score)
my_grove.add_edge(key1, key2, 0.95);
// Now key1 → key2 with weight 0.95
```

**Key Points:**

- Edges are directed (source → target)
- Edges can have optional metadata (third template parameter)
- Keys from different indices (chromosomes) can be linked
- The graph overlay shares the grove's lifetime

#### Parallel Edges (No Deduplication)

`add_edge(source, target)` appends to the source's adjacency list **unconditionally** — there is no
deduplication. Calling it twice with the same `(source, target)` creates two **parallel** edges. This is
intentional: parallel edges carrying distinct per-edge metadata are a legitimate use case.

Observable effects of adding the same edge `a → b` twice:

```cpp
my_grove.add_edge(a, b);
my_grove.add_edge(a, b);          // appends a second, parallel edge

my_grove.out_degree(a);           // == 2 (counts every edge)
my_grove.get_neighbors(a);        // == {b, b} (b appears twice)
my_grove.has_edge(a, b);          // == true (existence only, unaffected by count)
// get_edges(a) likewise reflects the duplicate (one metadata entry per edge)
```

Both edges are serialized into the `.gg` file.

**Other edge rules:**

- Self-edges are allowed: `add_edge(a, a)` is valid.
- A null `source` or `target` throws `std::invalid_argument`.

**Implication for callers:** if duplicate edges are undesirable, deduplicate **before** calling `add_edge`.
For example, the CLI's `idx --links` applier tracks seen `(source, target)` pairs in a `std::set` and skips
edges it has already added.

#### Building Graphs with Bulk Insert

When using bulk insert operations, you receive a vector of key pointers that can be directly used to create edges.
This is particularly useful when building graphs from large datasets or when the relationships between features
are defined in your input data.

```cpp
gst::grove<gdt::interval, std::string, double> my_grove(100);

// Bulk insert returns vector of key pointers
std::vector<std::pair<gdt::interval, std::string>> exon_data = {
    {{100, 200}, "exon1"}, {{300, 400}, "exon2"},
    {{500, 600}, "exon3"}, {{700, 800}, "exon4"}
};

auto exon_keys = my_grove.insert_data("chr1", exon_data, gst::sorted, gst::bulk);

// Link consecutive exons
for (size_t i = 0; i < exon_keys.size() - 1; ++i) {
    my_grove.add_edge(exon_keys[i], exon_keys[i + 1], 0.95);
}
```

#### Building graphs from query results

Query results also provide key handles, allowing you to build graphs based on spatial relationships or
other query criteria. This is useful when you want to create edges between features that meet certain
positional or biological criteria.

**Example: Linking overlapping features**

```cpp
gst::grove<gdt::interval, std::string, void> my_grove(100);

// Insert some genes
my_grove.insert_data("chr1", gdt::interval{1000, 2000}, "GeneA");
my_grove.insert_data("chr1", gdt::interval{1500, 2500}, "GeneB");
my_grove.insert_data("chr1", gdt::interval{2200, 3000}, "GeneC");
my_grove.insert_data("chr1", gdt::interval{5000, 6000}, "GeneD");

// Query for genes in a region
gdt::interval query_region{1000, 3000};
auto results = my_grove.intersect(query_region, "chr1");

// Get key handles from query results
const auto& overlapping_keys = results.get_keys();

// Create edges between all overlapping features
for (size_t i = 0; i < overlapping_keys.size(); ++i) {
    for (size_t j = i + 1; j < overlapping_keys.size(); ++j) {
        my_grove.add_edge(overlapping_keys[i], overlapping_keys[j]);
    }
}
// Creates edges: GeneA -> GeneB, GeneA -> GeneC, GeneB -> GeneC
// GeneD is not included (doesn't overlap query region)
```

**Example: Building proximity-based networks**

```cpp
gst::grove<gdt::interval, std::string, double> enhancer_grove(100);

// Insert enhancers and genes
auto* enhancer1 = enhancer_grove.insert_data("chr1", gdt::interval{1000, 1500}, "Enh1");
auto* enhancer2 = enhancer_grove.insert_data("chr1", gdt::interval{2000, 2500}, "Enh2");
enhancer_grove.insert_data("chr1", gdt::interval{5000, 10000}, "Gene1");
enhancer_grove.insert_data("chr1", gdt::interval{15000, 20000}, "Gene2");

// For each enhancer, find nearby genes (within 10kb)
gdt::interval search_window1{1000 - 10000, 1500 + 10000};
auto nearby_features1 = enhancer_grove.intersect(search_window1, "chr1");

// Link enhancer to nearby genes with distance-based confidence
for (auto* feature : nearby_features1.get_keys()) {
    if (feature != enhancer1) {  // Skip the enhancer itself
        // Calculate distance-based confidence score
        double confidence = 0.9;  // Example: would calculate from actual distance
        enhancer_grove.add_edge(enhancer1, feature, confidence);
    }
}
```

**Example: Combining insertion and query for incremental graph building**

```cpp
gst::grove<gdt::interval, std::string, void> pathway_grove(100);

// Insert a gene
auto* new_gene = pathway_grove.insert_data("chr1", gdt::interval{5000, 6000}, "GeneX");

// Find all genes that overlap with the new gene
auto overlapping = pathway_grove.intersect(new_gene->get_value(), "chr1");

// Link new gene to all overlapping genes
for (auto* existing_gene : overlapping.get_keys()) {
    if (existing_gene != new_gene) {  // Skip self
        pathway_grove.add_edge(new_gene, existing_gene);
    }
}
```

**Ways to obtain key handles:**

1. **Insert operations**

   - `insert_data()` - Returns single key pointer
   - `insert_data(..., sorted, bulk)` - Returns vector of key pointers

2. **Query operations**

   - `intersect()` returns `query_result`
   - Call `get_keys()` on result to get vector of key pointers
   - Use these pointers directly with `add_edge()`

3. **Graph navigation**

   - `get_neighbors()` - Returns vector of neighbor key pointers
   - Can be used to extend the graph further

### Adding Edges based on Condition (`link_if`)

The `link_if` function is a convenience method for creating edges between consecutive keys in a vector based
on a predicate. Instead of manually looping through pairs and calling `add_edge`, you can use `link_if` to
express the linking logic declaratively.

This is particularly useful after bulk insert operations where you want to connect adjacent keys only when they
satisfy certain criteria (e.g., belonging to the same transcript, within a distance threshold, etc.).

**Function Signature:**

```cpp
// Without metadata: predicate returns bool
template<typename Predicate>
void link_if(const std::vector<gdt::key<key_type, data_type>*>& keys, Predicate predicate)

// With metadata: predicate returns std::optional<EdgeMetadata>
template<typename Predicate>
void link_if(const std::vector<gdt::key<key_type, data_type>*>& keys, Predicate predicate)
```

**Parameters:**

- `keys` - Vector of key pointers (typically from `insert_data(..., sorted, bulk)` or query results)

- `predicate` - Function that determines if an edge should be created between consecutive keys

  - **Without metadata**: Takes two adjacent keys, returns `bool` (true = create edge)
  - **With metadata**: Takes two adjacent keys, returns `std::optional<EdgeMetadata>` (value = create edge with metadata, nullopt = no edge)

**Return Value:**

- Returns `void` (no return value)
- Edges are created internally based on predicate results

**Behavior:**

- Iterates through consecutive pairs: (keys[0], keys[1]), (keys[1], keys[2]), ..., (keys[n-2], keys[n-1])
- For each pair, evaluates the predicate
- Creates an edge from keys[i] → keys[i+1] if predicate condition is met

**Example: Linking exons from the same transcript**

```cpp
gst::grove<gdt::interval, TranscriptData, void> grove(100);

// Bulk insert exons (may belong to different transcripts)
std::vector<std::pair<gdt::interval, TranscriptData>> exon_data = {
    {{100, 200}, {"tx1", "exon1"}}, {{300, 400}, {"tx1", "exon2"}},
    {{500, 600}, {"tx2", "exon1"}}, {{700, 800}, {"tx2", "exon2"}}
};

auto exon_keys = grove.insert_data("chr1", exon_data, gst::sorted, gst::bulk);

// Link only exons from the same transcript
grove.link_if(exon_keys,
    [](auto* k1, auto* k2) {
        return k1->get_data().transcript_id == k2->get_data().transcript_id;
    });
// Creates edges: tx1_exon1 → tx1_exon2, tx2_exon1 → tx2_exon2
// No edge between tx1_exon2 and tx2_exon1 (different transcripts)
```

**Example: Linking based on distance threshold**

```cpp
gst::grove<gdt::interval, std::string, void> grove(100);

auto gene_keys = grove.insert_data("chr1", data, gst::sorted, gst::bulk);

// Link genes only if they're within 5000bp of each other
grove.link_if(gene_keys,
    [](auto* k1, auto* k2) {
        size_t gap = k2->get_value().get_start() - k1->get_value().get_end();
        return gap <= 5000;
    });
```

**Example: With metadata - calculating edge weights**

```cpp
gst::grove<gdt::interval, std::string, double> grove(100);

auto exon_keys = grove.insert_data("chr1", data, gst::sorted, gst::bulk);

// Link exons with intron length as edge weight
grove.link_if(exon_keys,
    [](auto* k1, auto* k2) -> std::optional<double> {
        size_t intron_length = k2->get_value().get_start() - k1->get_value().get_end();

        // Only link if intron is reasonable size (< 100kb)
        if (intron_length < 100000) {
            return static_cast<double>(intron_length);
        }
        return std::nullopt;  // No edge for very large gaps
    });
```

**Example: Combining query results with link_if**

```cpp
gst::grove<gdt::interval, GeneData, void> grove(100);

// Insert genes...
grove.insert_data("chr1", data, gst::sorted, gst::bulk);

// Query for genes in a specific region
auto results = grove.intersect(gdt::interval{1000, 10000}, "chr1");
const auto& region_genes = results.get_keys();

// Link genes in the region if they're on the same strand
grove.link_if(region_genes,
    [](auto* k1, auto* k2) {
        return k1->get_data().strand == k2->get_data().strand;
    });
```

**Key Benefits:**

- Declarative syntax - express linking logic clearly
- Automatic iteration through consecutive pairs
- Type-safe with lambda captures
- Works with both bulk insert results and query results
- Supports conditional edge creation with optional metadata

### External (Graph-only) Keys

Sometimes you need keys that participate in graph relationships but don't require spatial indexing. For example, transcription factors, regulatory elements, or abstract concepts that connect genomic features but aren't themselves genomic intervals you need to query spatially.

The `add_external_key` function creates keys that:

- **Can participate in graph edges** - work with `add_edge()`, `link_if()`, `get_neighbors()`, etc.
- **Are NOT indexed in the B+ tree** - won't appear in `intersect()` query results
- **Are owned by the grove** - automatically managed and serialized with the grove

**Function Signatures:**

```cpp
// With associated data
gdt::key<key_type, data_type>* add_external_key(key_type key_value, data_type data_value)

// Without associated data (when data_type is void)
gdt::key<key_type, data_type>* add_external_key(key_type key_value)
```

**Parameters:**

- `key_value` - The key value (e.g., interval) - required but not used for spatial queries
- `data_value` - Optional data associated with the key

**Return Value:**

- Pointer to the newly created external key (can be used with all graph operations)

**Example: Regulatory network with transcription factors**

```cpp
gst::grove<gdt::interval, std::string, double> grove(100);

// Insert genes (indexed - can be found via spatial queries)
auto* gene1 = grove.insert_data("chr1", gdt::interval{10000, 15000}, "BRCA1");
auto* gene2 = grove.insert_data("chr1", gdt::interval{20000, 25000}, "TP53");
auto* gene3 = grove.insert_data("chr1", gdt::interval{30000, 35000}, "MYC");

// Create external key for a transcription factor
// (participates in graph but not needed for spatial queries)
auto* tf = grove.add_external_key(gdt::interval{0, 0}, "E2F1_TF");

// Build regulatory network
grove.add_edge(tf, gene1, 0.95);  // TF regulates BRCA1
grove.add_edge(tf, gene2, 0.87);  // TF regulates TP53
grove.add_edge(tf, gene3, 0.72);  // TF regulates MYC

// Graph operations work normally
auto targets = grove.get_neighbors(tf);
std::cout << "E2F1 regulates " << targets.size() << " genes\n";
// Output: E2F1 regulates 3 genes

// Spatial query only returns indexed genes
gdt::interval query{5000, 40000};
auto results = grove.intersect(query, "chr1");
std::cout << "Genes in region: " << results.get_keys().size() << "\n";
// Output: Genes in region: 3 (tf is NOT included)
```

**Example: Linking indexed features to external nodes**

```cpp
gst::grove<gdt::interval, std::string, void> grove(100);

// Insert exons (indexed)
std::vector<gdt::key<gdt::interval, std::string>*> exons;
exons.push_back(grove.insert_data("chr1", gdt::interval{1000, 1200}, "exon1"));
exons.push_back(grove.insert_data("chr1", gdt::interval{2000, 2300}, "exon2"));
exons.push_back(grove.insert_data("chr1", gdt::interval{3000, 3150}, "exon3"));

// Create external key for transcript (abstract grouping)
auto* transcript = grove.add_external_key(gdt::interval{0, 0}, "ENST00000123");

// Link exons to their transcript
for (auto* exon : exons) {
    grove.add_edge(transcript, exon);
}

// Can navigate from transcript to exons
auto exon_list = grove.get_neighbors(transcript);
std::cout << "Transcript has " << exon_list.size() << " exons\n";
```

**Example: Using link_if with external keys**

```cpp
gst::grove<gdt::interval, std::string, void> grove(100);

// Insert indexed features
auto* exon1 = grove.insert_data("chr1", gdt::interval{1000, 1200}, "exon1");
auto* exon2 = grove.insert_data("chr1", gdt::interval{2000, 2300}, "exon2");

// Create external key
auto* sink = grove.add_external_key(gdt::interval{0, 0}, "sink_node");

// link_if works with mixed vectors containing both indexed and external keys
std::vector<gdt::key<gdt::interval, std::string>*> path = {exon1, exon2, sink};

grove.link_if(path, [](auto* k1, auto* k2) {
    return true;  // Link all consecutive pairs
});
// Creates: exon1 -> exon2 -> sink
```

**Vertex counting with external keys:**

```cpp
gst::grove<gdt::interval, std::string, void> grove(100);

// Insert 3 indexed keys
grove.insert_data("chr1", gdt::interval{100, 200}, "A");
grove.insert_data("chr1", gdt::interval{300, 400}, "B");
grove.insert_data("chr1", gdt::interval{500, 600}, "C");

// Add 2 external keys
grove.add_external_key(gdt::interval{0, 0}, "ext1");
grove.add_external_key(gdt::interval{0, 0}, "ext2");

std::cout << "Total vertices: " << grove.vertex_count() << "\n";
// Output: 5

std::cout << "Indexed vertices: " << grove.indexed_vertex_count() << "\n";
// Output: 3 (queryable via intersect)

std::cout << "External vertices: " << grove.external_vertex_count() << "\n";
// Output: 2 (graph-only)
```

**When to use external keys:**

- **Transcription factors** - regulate genes but don't need spatial queries
- **Abstract concepts** - transcript IDs, pathway nodes, sample identifiers
- **Graph sink/source nodes** - terminal nodes in directed graphs
- **Metadata nodes** - group features without spatial semantics
- **Cross-reference entities** - link to external databases or annotations

**Key benefits:**

- Keeps the B+ tree lean (only spatially-relevant data)
- Full graph functionality without spatial overhead
- Automatic serialization/deserialization with the grove
- Works seamlessly with `link_if()` and all graph operations

### Navigating the Graph

Query and navigate relationships between keys:

```cpp
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
    std::cout << "Vertices with edges: " << my_grove.vertex_count_with_edges() << "\n";

    // Remove an edge
    my_grove.remove_edge(exon2, exon3);

    // Clear all edges (keeps keys in grove)
    my_grove.clear_graph();

    return 0;
}
```

**Graph Methods:**

- `add_edge(source, target)` - Create edge without metadata
- `add_edge(source, target, metadata)` - Create edge with metadata
- `remove_edge(source, target)` - Remove specific edge
- `get_neighbors(source)` - Get all targets of outgoing edges
- `get_neighbors_if(source, predicate)` - Get filtered neighbors
- `has_edge(source, target)` - Check if edge exists
- `out_degree(source)` - Count outgoing edges from a key
- `edge_count()` - Total edges in the graph
- `vertex_count()` - Total number of keys in the grove (indexed + external)
- `indexed_vertex_count()` - Number of keys indexed in the B+ tree
- `external_vertex_count()` - Number of graph-only keys
- `clear_graph()` - Remove all edges (keeps keys in grove)

### Graph Overlay Without Metadata

If you don't need edge metadata, use `void` as the third template parameter:

```cpp
// No edge metadata
gst::grove<gdt::interval, std::string, void> my_grove(100);

auto* key1 = my_grove.insert_data("chr1", gdt::interval{100, 200}, "feature1");
auto* key2 = my_grove.insert_data("chr1", gdt::interval{300, 400}, "feature2");

// Add edge without metadata
my_grove.add_edge(key1, key2);

// Navigate normally
auto neighbors = my_grove.get_neighbors(key1);
```

### Using Different Key Types with Graph Overlay

The graph overlay works with any key type, including custom types:

```cpp
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
```

### Combining Interval Queries with Graph Navigation

A powerful pattern: query for intervals, then navigate their relationships:

```cpp
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
```

::::

::::{tab-item} {{ py_tab }}
:sync: py

Every grove carries an embedded **graph overlay** — directed edges between keys —
on top of its spatial B+ tree index. This lets you represent feature
relationships (exon→transcript, regulatory links, …) alongside interval queries.

### Edges between keys

```python
import pygenogrove as pg

g = pg.Grove()
a = g.insert("chr1", pg.GenomicCoordinate("+", 100, 200))
b = g.insert("chr1", pg.GenomicCoordinate("+", 300, 400))
g.add_edge(a, b)
g.has_edge(a, b)            # True
g.get_neighbors(a)         # [b]
g.out_degree(a)            # 1
```

- `add_edge(source: Key, target: Key)` — add a directed edge. Raises `ValueError`
  if either key is `None`.
- `remove_edge(source: Key, target: Key) -> bool` — remove an edge; `True` if one
  was removed.
- `has_edge(source: Key, target: Key) -> bool` — test whether an edge exists.
- `get_neighbors(source: Key) -> list[Key]` — keys directly reachable from `source`.
- `out_degree(source: Key) -> int` — number of outgoing edges from `source`.
- `edge_count() -> int` — total edges in the overlay.
- `vertex_count_with_edges() -> int` — keys with at least one outgoing edge.

:::{note}
`add_edge` does **not** deduplicate — calling it twice with the same `(source, target)` appends a second,
parallel edge. After a duplicate `a → b`: `out_degree(a) == 2`, `get_neighbors(a) == [b, b]`, but
`has_edge(a, b)` stays `True` (existence only). Both edges are written to the `.gg`. Deduplicate before
calling if duplicates are undesirable.
:::

### External keys

`add_external_key(key: GenomicCoordinate, data=None) -> Key` adds a graph-only key
that lives **outside** the B+ tree index: it participates in the graph but is
**not** returned by `intersect()`. Useful for anchoring graph nodes that are not
themselves query targets.

```python
ext = g.add_external_key(pg.GenomicCoordinate(".", 0, 0), {"label": "promoter"})
g.add_edge(ext, a)
```

External keys are **not** invalidated by `compact()` (unlike indexed keys — see
{doc}`./grove`).

### Labelled edges

On the **universal `Grove`**, edges carry a JSON-serializable payload. (The typed
`BedGrove` / `GffGrove` keep unlabelled edges for binary interop, so the
labelled-edge methods below are absent there — see {doc}`./loading_data`.)

```python
import pygenogrove as pg

g = pg.Grove()
a = g.insert("chr1", pg.GenomicCoordinate("+", 100, 200))
b = g.insert("chr1", pg.GenomicCoordinate("+", 300, 400))
g.add_edge(a, b, {"type": "exon->transcript", "weight": 7})
g.get_edges(a)                                    # [{"type": ..., "weight": 7}]
g.get_neighbors_if(a, lambda m: m["weight"] > 5)  # [b]
```

- `add_edge(source, target, data)` — add an edge with a metadata payload. The
  2-argument `add_edge` attaches `None`.
- `get_edges(source: Key) -> list` — the edge payloads of `source`'s outgoing
  edges, parallel to `get_neighbors(source)`.
- `get_neighbors_if(source: Key, predicate) -> list[Key]` — target keys whose edge
  metadata satisfies `predicate(metadata)`. The predicate receives the **decoded**
  payload (edges added without a payload yield `None`, so guard for it when mixing
  labelled and unlabelled edges).
- `link_with(keys: list[Key], predicate)` — label adjacent pairs: `predicate(k1, k2)`
  returns the edge payload to attach, or `None` to skip.

A canonical example is labelling exon→transcript edges with their intron gaps via
`link_with` over a chromosome's exon keys.

### Edge cleanup and bulk linking

Available on **every** grove (universal and typed):

- `remove_edges_from(source: Key) -> int` — remove outgoing edges; returns the count.
- `remove_edges_to(target: Key) -> int` — remove incoming edges; returns the count.
- `remove_all_edges(key: Key) -> int` — remove all edges touching `key`; returns the count.
- `remove_edges_if(predicate) -> int` — remove every edge whose predicate returns
  `True`; returns the count. The predicate signature differs by grove type: on the
  universal / point groves (`Grove`, `NumericGrove`, `KmerGrove`) it is
  `predicate(target: Key, metadata) -> bool`; on the typed groves (`BedGrove`,
  `GffGrove`) it is `predicate(target: Key) -> bool`.
- `clear_graph()` — remove all edges (keys are left intact).
- `graph_empty() -> bool` — whether the overlay has no edges.
- `link_if(keys: list[Key], predicate)` — add an **unlabelled** edge between each
  adjacent pair `(keys[i], keys[i+1])` for which `predicate(k1, k2)` returns
  `True` (typically over the keys returned by a bulk insert).

### SIF export

`grove.to_sif(path)` is available on **every** grove (`Grove`, `BedGrove`,
`GffGrove`, `NumericGrove`, `KmerGrove`). It writes the grove to a **SIF** (Simple
Interaction Format) text file for visualization in tools like Cytoscape. The
output is tab-separated interactions of three kinds:

- `nodelink` — an internal B+ tree node → child,
- `leaflink` — a leaf → its next leaf,
- `keylink` — a key → a graph-overlay neighbour (i.e. the edges added via
  `add_edge`).

Each key is rendered by its value's string form. An empty grove writes an empty
file. The GIL is released during the write.

:::{warning}
Line and index order are **not stable across runs** (index iteration follows a
hash map) — treat the output as a *set* of interactions, not an ordered list.
:::

```python
import pygenogrove as pg

g = pg.Grove()
a = g.insert("chr1", pg.GenomicCoordinate("+", 100, 200))
b = g.insert("chr1", pg.GenomicCoordinate("+", 300, 400))
g.add_edge(a, b)
g.to_sif("graph.sif")   # load graph.sif in Cytoscape
```

### Predicate callbacks

`remove_edges_if`, `link_if`, `link_with`, and `get_neighbors_if` all invoke a
Python predicate from C++ mid-iteration. Two caveats apply:

:::{warning}
**Partial effect if the predicate raises.** These methods apply their effect *as
they iterate*. If the Python predicate raises partway through, the exception
propagates to Python, but edges already matched/processed before the throw have
**already** been removed/added — there is no rollback. Validate inputs before
calling, or catch and reconcile.

**Do not mutate the graph from within the predicate.** The predicate runs while
genogrove iterates the adjacency structure. Calling `add_edge` /
`remove_edges_*` / `clear_graph` / `link_*` on the same grove from inside the
predicate is **undefined behavior** (crash / corruption). The predicate must be a
pure inspector of the `(target, metadata)` (or `(key, key)`) it is handed; do
graph mutation after the call returns.
:::

### Persistence

`serialize` / `deserialize` round-trip the graph overlay along with the
coordinates and payloads. An edge-bearing universal-`Grove` `.gg` stores per-edge
JSON metadata and is read in C++ as
`grove<genomic_coordinate, std::string, std::string>` (edgeless files are
unchanged). See {doc}`./grove` for the serialization API.

::::

:::::