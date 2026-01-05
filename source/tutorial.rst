Tutorial
========

This tutorial will guide you through using genogrove for common genomic data analysis tasks.

Prerequisites
-------------

Before starting this tutorial, make sure you have installed genogrove (see :doc:`home` for installation instructions)

Reading Genomic Files
---------------------

Genogrove provides

BED Files
~~~~~~~~~

BED files are a common format for genomic intervals. Here's how to read them:

.. code-block:: cpp

   #include <genogrove/io/bed_reader.hpp>
   #include <iostream>

   namespace gio = genogrove::io;

   int main() {
       gio::bed_reader reader("example.bed");

       for (const auto& entry : reader) {
           std::cout << "Chromosome: " << entry.chromosome << "\n"
                     << "Start: " << entry.interval.start << "\n"
                     << "End: " << entry.interval.end << "\n";
       }

       return 0;
   }

GFF/GTF Files
~~~~~~~~~~~~~

For gene annotation files:

.. code-block:: cpp

   #include <genogrove/io/gff_reader.hpp>

   namespace gio = genogrove::io;

   int main() {
       gio::gff_reader reader("annotations.gff");

       for (const auto& entry : reader) {
           // Process GFF entries
       }

       return 0;
   }

Working with Intervals
----------------------

Basic Operations
~~~~~~~~~~~~~~~~

.. code-block:: cpp

   #include <genogrove/data_type/interval.hpp>

   namespace gdt = genogrove::data_type;

   int main() {
       // Create intervals
       gdt::interval iv1{100, 200};
       gdt::interval iv2{150, 250};

       // Check for overlap
       if (iv1.overlaps(iv2)) {
           std::cout << "Intervals overlap\n";
       }

       // Calculate overlap length
       auto overlap = iv1.intersection(iv2);

       return 0;
   }

Genomic Coordinates
~~~~~~~~~~~~~~~~~~~

Working with strand-specific coordinates:

.. code-block:: cpp

   #include <genogrove/data_type/genomic_coordinate.hpp>

   namespace gdt = genogrove::data_type;

   int main() {
       // Create a coordinate with strand information
       gdt::genomic_coordinate coord{'+', 1000, 2000};

       // Access properties
       char strand = coord.strand;
       auto start = coord.start;
       auto end = coord.end;

       return 0;
   }

Using Grove Data Structure
---------------------------

Creating a Grove
~~~~~~~~~~~~~~~~

The grove is an order-based B+ tree variant optimized for interval queries:

.. code-block:: cpp

   #include <genogrove/structure/grove.hpp>
   #include <genogrove/data_type/interval.hpp>

   namespace gdt = genogrove::data_type;
   namespace gst = genogrove::structure;

   int main() {
       // Create a grove: key type, interval type, value type
       gst::grove<int, gdt::interval, std::string> my_grove;

       // Insert data
       my_grove.insert_data(1, gdt::interval{100, 200}, "gene1");
       my_grove.insert_data(2, gdt::interval{150, 250}, "gene2");
       my_grove.insert_data(3, gdt::interval{300, 400}, "gene3");

       return 0;
   }

Querying Intervals
~~~~~~~~~~~~~~~~~~

Find all intervals that overlap with a query:

.. code-block:: cpp

   #include <genogrove/structure/grove.hpp>
   #include <genogrove/data_type/interval.hpp>

   namespace gdt = genogrove::data_type;
   namespace gst = genogrove::structure;

   int main() {
       gst::grove<int, gdt::interval, std::string> my_grove;

       // Insert some intervals
       my_grove.insert_data(1, gdt::interval{100, 200}, "gene1");
       my_grove.insert_data(2, gdt::interval{150, 250}, "gene2");
       my_grove.insert_data(3, gdt::interval{300, 400}, "gene3");

       // Query for overlaps
       gdt::interval query{175, 225};
       auto results = my_grove.query(query);

       // Process results
       for (const auto& result : results) {
           // Handle overlapping intervals
       }

       return 0;
   }

Advanced Topics
---------------

Graph Overlays
~~~~~~~~~~~~~~

Genogrove supports graph overlays for representing relationships between genomic features.

.. code-block:: cpp

   // Coming soon: graph overlay examples

Performance Optimization
~~~~~~~~~~~~~~~~~~~~~~~~

Tips for optimizing performance with large genomic datasets:

- Use appropriate B+ tree order for your dataset size
- Consider memory vs. speed tradeoffs when choosing data structures
- Leverage compressed file formats when disk I/O is the bottleneck

Next Steps
----------

- Explore the full :doc:`reference` for detailed API documentation
- Check the `examples directory <https://github.com/genogrove/genogrove/tree/main/examples>`_ in the repository
- Read about advanced features in the project wiki