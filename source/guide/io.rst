Reading Genomic Files (I/O)
============================

The ``genogrove::io`` namespace provides efficient readers for common genomic file formats with automatic compression detection.

Automatic File Type Detection
------------------------------

Genogrove can automatically detect file types and compression formats:

.. code-block:: cpp

   #include <genogrove/io/filetype_detector.hpp>

   namespace gio = genogrove::io;

   int main() {
       auto [filetype, compression] = gio::filetype_detector::detect_filetype("data.bed.gz");

       // filetype will be gio::filetype::BED
       // compression will be gio::compression_type::GZIP

       return 0;
   }

**Supported File Types:**

- BED (Browser Extensible Data)
- BEDGRAPH
- GFF (General Feature Format)
- GTF (Gene Transfer Format)
- VCF (Variant Call Format)
- GG (Genogrove native format)

**Supported Compression Formats:**

- GZIP (.gz, including BGZF)
- BZIP2 (.bz2)
- XZ (.xz, LZMA)
- ZSTD (.zst)
- LZ4 (.lz4)

BED Files
---------

BED files store genomic intervals with optional metadata. The ``bed_reader`` provides iterator-based access:

.. code-block:: cpp

   #include <genogrove/io/bed_reader.hpp>
   #include <iostream>

   namespace gio = genogrove::io;

   int main() {
       // Automatically handles compressed files (.bed.gz)
       gio::bed_reader reader("example.bed");

       for (const auto& entry : reader) {
           std::cout << "Chromosome: " << entry.chrom << "\n"
                     << "Start: " << entry.interval.start << "\n"
                     << "End: " << entry.interval.end << "\n";

           // Optional fields (if present in file)
           if (!entry.name.empty()) {
               std::cout << "Name: " << entry.name << "\n";
           }
           if (entry.strand) {
               std::cout << "Strand: " << *entry.strand << "\n";
           }
       }

       return 0;
   }

**BED Entry Fields:**

- ``chrom`` (string): Chromosome name
- ``interval``: Genomic interval (0-based, half-open)
- ``name`` (optional): Feature name
- ``score`` (optional): Score value
- ``strand`` (optional): Strand (+/-)
- ``thick_start``, ``thick_end`` (optional): Display coordinates
- ``item_rgb`` (optional): RGB color value
- ``block_count`` (optional): Number of blocks
- ``block_sizes``, ``block_starts`` (optional): Block information

GFF/GTF Files
-------------

GFF3 and GTF files contain gene annotations. Genogrove automatically detects the format variant:

.. code-block:: cpp

   #include <genogrove/io/gff_reader.hpp>

   namespace gio = genogrove::io;

   int main() {
       gio::gff_reader reader("annotations.gff");

       for (const auto& entry : reader) {
           std::cout << "Sequence: " << entry.seqid << "\n"
                     << "Type: " << entry.type << "\n"
                     << "Start: " << entry.interval.start << "\n"
                     << "End: " << entry.interval.end << "\n";

           // GFF/GTF entries are 1-based but converted to 0-based intervals

           // Access attributes (column 9)
           if (auto gene_id = entry.get_gene_id()) {
               std::cout << "Gene ID: " << *gene_id << "\n";
           }

           // Check format
           if (entry.is_gtf()) {
               std::cout << "Format: GTF\n";
           } else if (entry.is_gff3()) {
               std::cout << "Format: GFF3\n";
           }
       }

       return 0;
   }

**GFF Entry Fields:**

- ``seqid`` (string): Chromosome/contig name
- ``source`` (string): Source of feature
- ``type`` (string): Feature type (gene, exon, CDS, etc.)
- ``interval``: Genomic interval (converted to 0-based)
- ``score`` (optional): Score value
- ``strand`` (optional): Strand (+, -, ., or ?)
- ``phase`` (optional): Phase for CDS features (0, 1, 2)
- ``attributes`` (map): Key-value pairs from column 9
- ``format``: Detected format (GFF3 or GTF)

**Helper Methods for Attributes:**

- ``get_gene_id()`` - Extract gene_id
- ``get_transcript_id()`` - Extract transcript_id
- ``get_exon_number()`` - Extract exon_number
- ``get_gene_name()`` - Extract gene_name
- ``get_gene_biotype()`` - Extract gene_biotype/gene_type
- ``get_attribute(key)`` - Generic attribute getter