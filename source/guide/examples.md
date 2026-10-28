# Complete Examples

End-to-end programs that combine what the guide covers one topic at a time: reading a file into a
grove, querying it, linking keys with the graph overlay, and saving the result to disk. Each
section is one complete program in both languages. The file names are placeholders; point them at
your own data.

## Processing BED files

Read a BED file into a grove keyed by chromosome and report the features overlapping one region.

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

```cpp
#include <genogrove/io/bed_reader.hpp>
#include <genogrove/structure/grove/grove.hpp>
#include <genogrove/data_type/interval.hpp>
#include <iostream>

namespace gio = genogrove::io;
namespace gdt = genogrove::data_type;
namespace gst = genogrove::structure;

int main() {
    // Create grove to store BED entries
    gst::grove<gdt::interval, std::string> features(100);

    // Read BED file (handles .bed.gz automatically)
    gio::bed_reader reader("data.bed.gz");

    try {
        for (const auto& entry : reader) {
            // Insert into grove (organized by chromosome)
            // Convert half-open [start, end) to closed [start, end - 1]
            features.insert_data(
                entry.chrom,
                gdt::interval(entry.start, entry.end - 1),
                entry.name.value_or("unnamed"),
                gst::sorted  // BED files are typically sorted
            );
        }
    } catch (const std::runtime_error& e) {
        std::cerr << "Error: " << e.what() << "\n";
    }

    // Query for overlapping features
    gdt::interval query_region{1000, 2000};
    auto results = features.intersect(query_region, "chr1");

    std::cout << "Found " << results.get_keys().size()
              << " features overlapping region\n";

    for (auto* key : results.get_keys()) {
        std::cout << "  - " << key->get_data()
                  << " at " << key->get_value().to_string() << "\n";
    }

    return 0;
}
```

`gst::sorted` promises that the file is position-sorted within each chromosome; drop it for an
unsorted file (see {doc}`grove/inserting`).

::::

::::{tab-item} {{ py_tab }}
:sync: py

```python
import pygenogrove as pg

# Create a typed grove to store BED entries
g = pg.BedGrove(100)

# Read the BED file (handles .bed.gz automatically) and insert each entry, keyed by chromosome
for e in pg.BedReader("data.bed.gz"):
    g.insert(e.chrom, e)               # key derived from each entry: [start, end - 1] plus strand

# Query for features overlapping chr1:1000-2000 on either strand
query = pg.GenomicCoordinate("*", 1000, 2000)
hits = g.intersect(query, "chr1")

print(f"Found {len(hits)} features overlapping region")
for hit in hits:
    print("  -", hit.data.name, "at", hit.value.start, hit.value.end)
```

`BedGrove.insert(index, entry)` derives the key from the entry's coordinates and strand, so the
`"*"` wildcard in the query is what makes it match features on any strand. See
{doc}`grove/loading_data`.

::::

:::::

## Processing GFF/GTF files

Read an annotation file, keep only `gene` features, and look up one attribute per hit. GFF/GTF
coordinates are 1-based closed, so both ends shift down by one.

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

```cpp
#include <genogrove/io/gff_reader.hpp>
#include <genogrove/structure/grove/grove.hpp>
#include <genogrove/data_type/genomic_coordinate.hpp>
#include <iostream>

namespace gio = genogrove::io;
namespace gdt = genogrove::data_type;
namespace gst = genogrove::structure;

struct GeneAnnotation {
    std::string gene_id;
    std::string gene_name;
    std::string type;
};

int main() {
    // Create grove with strand-aware coordinates
    gst::grove<gdt::genomic_coordinate, GeneAnnotation> annotations(100);

    // Read GFF file
    gio::gff_reader reader("annotations.gff.gz");

    try {
        for (const auto& entry : reader) {
            // Only process gene features
            if (entry.type != "gene") continue;

            // Create genomic coordinate with strand (GFF is 1-based inclusive;
            // shift to the grove's 0-based closed keys)
            gdt::genomic_coordinate coord{
                entry.strand.value_or('.'),
                entry.start - 1,
                entry.end - 1
            };

            // Extract annotation info
            GeneAnnotation annot{
                entry.get_gene_id().value_or("unknown"),
                entry.get_gene_name().value_or("unknown"),
                entry.type
            };

            // Insert into grove
            annotations.insert_data(
                entry.seqid,
                coord,
                annot,
                gst::sorted
            );
        }
    } catch (const std::runtime_error& e) {
        std::cerr << "Error: " << e.what() << "\n";
    }

    // Query for genes in a region
    gdt::genomic_coordinate query{'+', 5000, 10000};
    auto results = annotations.intersect(query, "chr1");

    std::cout << "Found " << results.get_keys().size() << " genes\n";
    for (auto* key : results.get_keys()) {
        auto& annot = key->get_data();
        std::cout << "  Gene: " << annot.gene_name
                  << " (ID: " << annot.gene_id << ")\n";
    }

    return 0;
}
```

::::

::::{tab-item} {{ py_tab }}
:sync: py

```python
import pygenogrove as pg

# A typed grove: every key carries the full GffEntry record
annotations = pg.GffGrove(100)

# Read the GFF/GTF file (handles .gz automatically); keep gene features only
for e in pg.GffReader("annotations.gff.gz"):
    if e.type != "gene":
        continue
    annotations.insert(e.seqid, e)     # key derived from the entry: [start - 1, end - 1] plus strand

# Query for genes on the + strand in chr1:5000-10000
query = pg.GenomicCoordinate("+", 5000, 10000)
hits = annotations.intersect(query, "chr1")

print(f"Found {len(hits)} genes")
for hit in hits:
    gene = hit.data                    # the stored GffEntry
    print("  Gene:", gene.get_gene_name() or "unknown", "(ID:", gene.get_gene_id() or "unknown", ")")
```

`GffGrove.insert(index, entry)` does the 1-based to 0-based shift for you. The named attribute
helpers (`get_gene_id()`, `get_gene_name()`, `get_transcript_id()`, …) return `None` when the
attribute is absent; `get_attribute(key)` reads any other one. See {doc}`io/gff`.

::::

:::::

## Building transcript graphs

Read the exons of a GFF file, group them by transcript, and chain consecutive exons of each
transcript with directed edges, so the graph overlay can answer "which exon comes next?".

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

```cpp
#include <genogrove/io/gff_reader.hpp>
#include <genogrove/structure/grove/grove.hpp>
#include <genogrove/data_type/interval.hpp>
#include <genogrove/data_type/key.hpp>
#include <iostream>
#include <map>
#include <string>
#include <vector>

namespace gio = genogrove::io;
namespace gdt = genogrove::data_type;
namespace gst = genogrove::structure;

int main() {
    // Grove with no edge metadata
    gst::grove<gdt::interval, std::string> transcripts(100);

    // Map to track exons per transcript
    std::map<std::string, std::vector<gdt::key<gdt::interval, std::string>*>>
        transcript_exons;

    // Read GFF file
    gio::gff_reader reader("transcripts.gff");

    try {
        for (const auto& entry : reader) {
            if (entry.type != "exon") continue;

            auto transcript_id = entry.get_transcript_id().value_or("unknown");

            // Insert exon (GFF is 1-based inclusive; shift to 0-based closed)
            auto* exon_key = transcripts.insert_data(
                entry.seqid,
                gdt::interval(entry.start - 1, entry.end - 1),
                transcript_id,
                gst::sorted
            );

            // Track exon for this transcript
            transcript_exons[transcript_id].push_back(exon_key);
        }
    } catch (const std::runtime_error& e) {
        std::cerr << "Error: " << e.what() << "\n";
    }

    // Build graph by connecting consecutive exons in each transcript
    for (auto& [transcript_id, exons] : transcript_exons) {
        for (size_t i = 0; i + 1 < exons.size(); ++i) {
            transcripts.add_edge(exons[i], exons[i + 1]);
        }
    }

    // Analyze transcript structure
    std::cout << "Transcript analysis:\n";
    for (auto& [transcript_id, exons] : transcript_exons) {
        std::cout << "  " << transcript_id << ": "
                  << exons.size() << " exons\n";

        // Show connectivity
        for (auto* exon : exons) {
            auto neighbors = transcripts.get_neighbors(exon);
            if (!neighbors.empty()) {
                std::cout << "    Exon at "
                          << exon->get_value().to_string()
                          << " connects to " << neighbors.size()
                          << " downstream exon(s)\n";
            }
        }
    }

    return 0;
}
```

::::

::::{tab-item} {{ py_tab }}
:sync: py

```python
import pygenogrove as pg
from collections import defaultdict

transcripts = pg.GffGrove(100)

# Insert every exon and remember its key under its transcript
transcript_exons = defaultdict(list)
for e in pg.GffReader("transcripts.gff"):
    if e.type != "exon":
        continue
    key = transcripts.insert(e.seqid, e)
    transcript_exons[e.get_transcript_id() or "unknown"].append(key)

# Chain consecutive exons of each transcript with directed edges
for exons in transcript_exons.values():
    for a, b in zip(exons, exons[1:]):
        transcripts.add_edge(a, b)

# Analyze transcript structure
print("Transcript analysis:")
for transcript_id, exons in transcript_exons.items():
    print(f"  {transcript_id}: {len(exons)} exons")
    for exon in exons:
        downstream = transcripts.get_neighbors(exon)
        if downstream:
            print(f"    Exon at {exon.value.start}-{exon.value.end} connects to "
                  f"{len(downstream)} downstream exon(s)")
```

The exons of one transcript are inserted in file order, so chaining them in list order gives
transcription order for a sorted file. `GffGrove` edges carry no metadata; use the universal
`Grove` when an edge needs a label (see {doc}`graph/building`).

::::

:::::

## Saving and reloading

Build a grove once, save it, and load it back in a later run — or query the file on disk without
loading all of it. Continues from the BED example above.

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

```cpp
#include <genogrove/structure/grove/grove.hpp>
#include <genogrove/structure/grove/grove_view.hpp>
#include <genogrove/data_type/interval.hpp>
#include <fstream>
#include <iostream>

namespace gdt = genogrove::data_type;
namespace gst = genogrove::structure;

int main() {
    gst::grove<gdt::interval, std::string> features(100);
    features.insert_data("chr1", gdt::interval{1000, 1500}, "gene1");
    features.insert_data("chr1", gdt::interval{1800, 2200}, "gene2");

    // Save
    {
        std::ofstream out("features.gg", std::ios::binary);
        features.serialize(out);
    }

    // Reload the whole grove (a later run would start here)
    {
        std::ifstream in("features.gg", std::ios::binary);
        auto reloaded = gst::grove<gdt::interval, std::string>::deserialize(in);
        auto hits = reloaded.intersect(gdt::interval{1000, 2000}, "chr1");
        std::cout << hits.get_keys().size() << " hits after reload\n";   // 2
    }

    // Or query the file in place, loading only the blocks the query touches
    auto view = gst::grove_view<gdt::interval, std::string>::open("features.gg");
    auto hits = view.intersect(gdt::interval{1000, 2000}, "chr1");
    std::cout << hits.get_keys().size() << " hits from the view\n";      // 2

    return 0;
}
```

The template arguments of `deserialize` and `grove_view::open` must match the grove that wrote the
file. See {doc}`serialization/index` and {doc}`serialization/partial_reading`.

::::

::::{tab-item} {{ py_tab }}
:sync: py

```python
import pygenogrove as pg

g = pg.BedGrove(100)
for e in pg.BedReader("data.bed.gz"):
    g.insert(e.chrom, e)

# Save
g.serialize("features.gg")

# Reload the whole grove (a later run would start here)
reloaded = pg.BedGrove.deserialize("features.gg")
hits = reloaded.intersect(pg.GenomicCoordinate("*", 1000, 2000), "chr1")
print(len(hits), "hits after reload")

# Or query the file in place, loading only the blocks the query touches
view = pg.BedGroveView.open("features.gg")
hits = view.intersect(pg.GenomicCoordinate("*", 1000, 2000), "chr1")
print(len(hits), "hits from the view")
```

Load a file with the grove class that wrote it (`BedGrove.deserialize` / `BedGroveView.open` for a
`BedGrove` file). See {doc}`serialization/index` and {doc}`serialization/partial_reading`.

::::

:::::