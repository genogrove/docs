# Complete Examples

End-to-end programs that combine what the guide covers one topic at a time: reading a file into a
grove, querying it, linking keys with the {term}`graph overlay`, and saving the result to disk.
Each section is one complete program in both languages; build and run them exactly as in step 3
of the {doc}`quickstart`. The file names are placeholders: point them at your own data, and each
section says what the file must contain for the query to find something.

## Processing BED files

Read a BED file into a grove keyed by chromosome and report the features overlapping one region.
The program prints `Found N features overlapping region` and then one line per hit; for a non-zero
`N`, `data.bed.gz` must have features on `chr1` between positions 1000 and 2000. The C++ version
stores the name as the payload; the Python version stores the whole `BedEntry`.

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
                entry.name.value_or("unnamed")
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

Plain inserts accept records in any order. For a large file that is sorted by start, then end, see
{doc}`grove/inserting` for the faster sorted and bulk inserts.

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
    print(f"  - {hit.data.name or 'unnamed'} at [{hit.value.start},{hit.value.end}]")
```

`BedGrove.insert(index, entry)` derives the key from the entry's coordinates and strand, so the
`"*"` wildcard in the query is what makes it match features on any strand. See
{doc}`grove/loading_data`.

::::

:::::

## Processing GFF/GTF files

Read an annotation file, keep only `gene` features, and look up one attribute per hit. GFF/GTF
coordinates are 1-based closed, so both ends shift down by one. The program prints `Found N genes`
and one line per hit; for a non-zero `N`, `annotations.gff.gz` needs `gene` lines on the `+`
strand of `chr1` between positions 5000 and 10000. The C++ version copies three fields into its
own payload record; the Python version stores the whole `GffEntry`.

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
            // shift to the grove's 0-based closed keys). GFF allows '?' for an
            // unknown strand; the coordinate type does not, so treat it as '.'.
            char strand = entry.strand.value_or('.');
            if (strand == '?') strand = '.';
            gdt::genomic_coordinate coord{strand, entry.start - 1, entry.end - 1};

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
                annot
            );
        }
    } catch (const std::runtime_error& e) {
        std::cerr << "Error: " << e.what() << "\n";
    }

    // Query for genes on the + strand in a region ('*' would match either strand)
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

`get_gene_id()`, `get_gene_name()` and the other named attribute helpers return a
`std::optional`, empty when the attribute is absent, hence `value_or`. `get_attribute(key)` reads
any other attribute. See {doc}`io/gff`.

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
    print(f"  Gene: {gene.get_gene_name() or 'unknown'} (ID: {gene.get_gene_id() or 'unknown'})")
```

`GffGrove.insert(index, entry)` does the 1-based to 0-based shift for you. The named attribute
helpers (`get_gene_id()`, `get_gene_name()`, `get_transcript_id()`, …) return `None` when the
attribute is absent; `get_attribute(key)` reads any other one. See {doc}`io/gff`.

::::

:::::

## Building transcript graphs

Read the exons of a GTF file, group them by transcript, and chain consecutive exons of each
transcript with directed {term}`edges <edge>` in transcription order, so the graph overlay can
answer "which exon comes next?". The program prints one line per transcript and one per exon that
has a downstream neighbour. The C++ version stores the transcript id as the payload; the Python
version stores the whole `GffEntry`.

The input must be **GTF**: the example groups exons by `get_transcript_id()`, which reads the GTF
`transcript_id` attribute. GFF3 exons name their transcript in `Parent` instead, so on a GFF3 file
every exon would land under `"unknown"`; use `get_attribute("Parent")` there (the helpers are to
become format-aware, see [genogrove#594](https://github.com/genogrove/genogrove/issues/594)).

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

```cpp
#include <genogrove/io/gff_reader.hpp>
#include <genogrove/structure/grove/grove.hpp>
#include <genogrove/data_type/interval.hpp>
#include <genogrove/data_type/key.hpp>
#include <algorithm>
#include <iostream>
#include <map>
#include <string>
#include <vector>

namespace gio = genogrove::io;
namespace gdt = genogrove::data_type;
namespace gst = genogrove::structure;

int main() {
    // Grove whose edges carry no metadata (the default)
    gst::grove<gdt::interval, std::string> transcripts(100);

    // transcript id -> the key handles of its exons, and the transcript's strand
    std::map<std::string, std::vector<gdt::key<gdt::interval, std::string>*>> transcript_exons;
    std::map<std::string, char> transcript_strand;

    // Read GTF file
    gio::gff_reader reader("transcripts.gtf");

    try {
        for (const auto& entry : reader) {
            if (entry.type != "exon") continue;

            auto transcript_id = entry.get_transcript_id().value_or("unknown");

            // Insert exon (GTF is 1-based inclusive; shift to 0-based closed).
            // This time the returned key handle is kept: edges are added between handles.
            auto* exon_key = transcripts.insert_data(
                entry.seqid,
                gdt::interval(entry.start - 1, entry.end - 1),
                transcript_id
            );

            transcript_exons[transcript_id].push_back(exon_key);
            transcript_strand[transcript_id] = entry.strand.value_or('+');
        }
    } catch (const std::runtime_error& e) {
        std::cerr << "Error: " << e.what() << "\n";
    }

    // Put each transcript's exons in transcription order: ascending by position on the
    // + strand, descending on the - strand (a position-sorted file lists them ascending).
    for (auto& [transcript_id, exons] : transcript_exons) {
        std::sort(exons.begin(), exons.end(), [](auto* a, auto* b) {
            return a->get_value().get_start() < b->get_value().get_start();
        });
        if (transcript_strand[transcript_id] == '-') std::reverse(exons.begin(), exons.end());
    }

    // Build graph by connecting each exon to the next one of the same transcript
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

        // Show connectivity: get_neighbors returns the keys this exon points to
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

`interval` keys carry no strand, so the transcript's strand is remembered separately from the GTF
line. Edges and `get_neighbors` are explained in {doc}`graph/building` and {doc}`graph/navigating`.

::::

::::{tab-item} {{ py_tab }}
:sync: py

```python
import pygenogrove as pg
from collections import defaultdict

transcripts = pg.GffGrove(100)

# Insert every exon and remember its key handle under its transcript
# (this time the handle is kept: edges are added between handles)
transcript_exons = defaultdict(list)
for e in pg.GffReader("transcripts.gtf"):
    if e.type != "exon":
        continue
    key = transcripts.insert(e.seqid, e)
    transcript_exons[e.get_transcript_id() or "unknown"].append(key)

# Put each transcript's exons in transcription order: ascending by position on the
# + strand, descending on the - strand (a position-sorted file lists them ascending)
for exons in transcript_exons.values():
    exons.sort(key=lambda k: k.value.start, reverse=(exons[0].value.strand == "-"))

# Connect each exon to the next one of the same transcript with a directed edge
for exons in transcript_exons.values():
    for a, b in zip(exons, exons[1:]):
        transcripts.add_edge(a, b)

# Analyze transcript structure: get_neighbors returns the keys this exon points to
print("Transcript analysis:")
for transcript_id, exons in transcript_exons.items():
    print(f"  {transcript_id}: {len(exons)} exons")
    for exon in exons:
        downstream = transcripts.get_neighbors(exon)
        if downstream:
            print(f"    Exon at [{exon.value.start},{exon.value.end}] connects to "
                  f"{len(downstream)} downstream exon(s)")
```

The key's coordinate carries the strand, so each transcript's direction is read from its first
exon. `GffGrove` edges carry no metadata; use the universal `Grove` when an edge needs a label
(see {doc}`graph/building`).

::::

:::::

## Saving and reloading

Build a grove once, save it, and load it back in a later run — or query the file on disk through a
{term}`view` without loading all of it. Both programs are self-contained: two hand-inserted
intervals, so each prints `2` twice.

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

    // Save: open the file for writing in binary mode; the closing brace closes it
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

The `<gdt::interval, std::string>` part of `deserialize` and `grove_view::open` (the
{term}`template` arguments) must be the same as when the file was saved. C++ reads and writes
streams; the Python API takes a file name. See {doc}`serialization/index` and
{doc}`serialization/partial_reading`.

::::

::::{tab-item} {{ py_tab }}
:sync: py

```python
import pygenogrove as pg

features = pg.Grove(100)
features.insert("chr1", pg.GenomicCoordinate("+", 1000, 1500), {"name": "gene1"})
features.insert("chr1", pg.GenomicCoordinate("+", 1800, 2200), {"name": "gene2"})

# Save
features.serialize("features.gg")

# Reload the whole grove (a later run would start here)
reloaded = pg.Grove.deserialize("features.gg")
hits = reloaded.intersect(pg.GenomicCoordinate("*", 1000, 2000), "chr1")
print(len(hits), "hits after reload")          # 2

# Or query the file in place, loading only the blocks the query touches
view = pg.GroveView.open("features.gg")
hits = view.intersect(pg.GenomicCoordinate("*", 1000, 2000), "chr1")
print(len(hits), "hits from the view")         # 2
```

Load a file with the grove class that wrote it: `Grove.deserialize` / `GroveView.open` here,
`BedGrove.deserialize` / `BedGroveView.open` for a `BedGrove` such as the one in the BED example.
See {doc}`serialization/index` and {doc}`serialization/partial_reading`.

::::

:::::