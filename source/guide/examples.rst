Complete Examples
==================

Processing BED Files
--------------------

Here's a complete workflow combining file I/O, data structures, and queries:

.. code-block:: cpp

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

       // Read BED file
       gio::bed_reader reader("data.bed.gz");

       for (const auto& entry : reader) {
           // Insert into grove (organized by chromosome)
           features.insert_data(
               entry.chrom,
               entry.interval,
               entry.name.empty() ? "unnamed" : entry.name,
               gst::sorted  // BED files are typically sorted
           );
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

Processing GFF/GTF Files
------------------------

Working with gene annotations:

.. code-block:: cpp

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

       for (const auto& entry : reader) {
           // Only process gene features
           if (entry.type != "gene") continue;

           // Create genomic coordinate with strand
           gdt::genomic_coordinate coord{
               entry.strand.value_or('.'),
               entry.interval.start,
               entry.interval.end
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

Building Transcript Graphs
--------------------------

Representing transcript structures with graph overlays:

.. code-block:: cpp

   #include <genogrove/io/gff_reader.hpp>
   #include <genogrove/structure/grove/grove.hpp>
   #include <genogrove/data_type/interval.hpp>
   #include <map>
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

       for (const auto& entry : reader) {
           if (entry.type != "exon") continue;

           auto transcript_id = entry.get_transcript_id().value_or("unknown");

           // Insert exon
           auto* exon_key = transcripts.insert_data(
               entry.seqid,
               entry.interval,
               transcript_id,
               gst::sorted
           );

           // Track exon for this transcript
           transcript_exons[transcript_id].push_back(exon_key);
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