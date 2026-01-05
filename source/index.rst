.. genogrove documentation master file, created by
   sphinx-quickstart on Wed Aug 20 17:14:01 2025.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. genogrove documentation
.. =======================

.. Add your content using ``reStructuredText`` syntax. See the
.. `reStructuredText <https://www.sphinx-doc.org/en/master/usage/restructuredtext/index.html>`_
.. documentation for details.

genogrove
=========

A high-performance modern C++ library for genomic data structures.

What is genogrove?
------------------

Genogrove provides efficient data structures and I/O utilities for working with genomic data. It features an
order-based hybrid tree graph structure for efficient storage and querying.

Getting Started
===============

Installation
------------

1. Clone the repository:

   .. code-block:: bash

      git clone https://github.com/genogrove/genogrove.git
      cd genogrove

2. Build the project using CMake:

   .. code-block:: bash

      cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
      cmake --build build

3. Run tests (optional):

   .. code-block:: bash

      ctest -C Release

   Note: This requires CMake to be called with ``-DBUILD_TESTING=ON``

4. Include in your project:

   - Add ``genogrove/include`` to your include path
   - Link against the built library in your CMake or build system

Basic Usage
-----------

Reading BED files
~~~~~~~~~~~~~~~~~

.. code-block:: cpp

   #include <genogrove/io/bed_reader.hpp>

   namespace gio = genogrove::io

   gio::bed_reader reader("input.bed");

   for (const auto& entry : reader) {
       std::cout << entry.chromosome << "\t"
                 << entry.interval.start << "\t"
                 << entry.interval.end << std::endl;
   }

Working with intervals
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: cpp

   #include <genogrove/data_type/interval.hpp>
   #include <genogrove/data_type/genomic_coordinate.hpp>

   namespace gdt = genogrove::data_type;

   // Basic interval
   gdt::interval iv1{100, 200};
   gdt::interval iv2{150, 250};

   // Check for overlap
   bool overlaps = iv1.overlaps(iv2);  // true

   // Genomic coordinate with strand
   gdt::genomic_coordinate coord{'+', 1000, 2000};

Using the grove data structure
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: cpp

   #include <genogrove/structure/grove.hpp>
   #include <genogrove/data_type/interval.hpp>

   namespace gdt = genogrove::data_type
   namespace gst = genogrove::structure;

   // Create a grove for interval storage
   gst::grove<int, gdt::interval, void> my_grove;

   // Insert intervals with keys
   my_grove.insert_data(1, gdt::interval{100, 200});
   my_grove.insert_data(2, gdt::interval{150, 250});

   // Query overlapping intervals
   auto results = my_grove.query(data_type::interval{175, 225});

Requirements
------------

- C++20 compatible compiler (GCC 12+, Clang 14+)
- CMake 3.15 or higher
- htslib (for compressed file support)

Development
-----------

For development, you can run sanitizers (AddressSanitizer and UndefinedBehaviorSanitizer) to catch memory issues and undefined behavior. See the repository's ``SANITIZERS.md`` for details.

Next Steps
----------

- Explore the :doc:`reference` for detailed class and method documentation
- Check out the `GitHub repository <https://github.com/genogrove/genogrove>`_ for examples and source code

License
-------

Distributed under `GPLv3 <https://www.gnu.org/licenses/gpl-3.0.en.html>`_

.. toctree::
   :maxdepth: 2
   :caption: Home

   index
   tutorial
   reference
   cli

.. .. toctree::
..    :maxdepth: 2
..    :caption: Tutorial
..
..    tutorial
..
.. .. toctree::
..    :maxdepth: 2
..    :caption: Reference
..
..    reference
..
.. .. toctree::
..    :maxdepth: 1
..    :caption: CLI
..
..    cli
