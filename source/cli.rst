CLI
===

Genogrove provides a command-line interface for indexing interval files and performing intersection queries without writing code.

Getting Started
---------------

After building genogrove with CLI support, the ``genogrove`` executable provides two main subcommands:

- ``idx`` - Index an interval file
- ``isec`` - Search for interval overlaps

To see available subcommands:

.. code-block:: bash

   genogrove --help

Subcommands
-----------

idx (Index)
~~~~~~~~~~~

The ``idx`` subcommand creates an index from an interval file for efficient queries.

**Usage:**

.. code-block:: bash

   genogrove idx [OPTIONS] <inputfile>

**Arguments:**

.. list-table::
   :widths: 20 60 20
   :header-rows: 1

   * - Argument
     - Description
     - Required
   * - ``<inputfile>``
     - The input interval file to be indexed
     - Yes

**Options:**

.. list-table::
   :widths: 25 55 20
   :header-rows: 1

   * - Option
     - Description
     - Default
   * - ``-o, --outputfile``
     - Write the index to the specified file
     - ``<inputfile>.gg``
   * - ``-k, --order``
     - The order of the B+ tree
     - 3
   * - ``-s, --sorted``
     - Indicate that intervals in the input file are pre-sorted
     - false
   * - ``-t, --timed``
     - Measure and display the time taken for indexing
     - false
   * - ``-h, --help``
     - Print help information
     -

**Example:**

.. code-block:: bash

   # Index a BED file
   genogrove idx genes.bed

   # Index with custom tree order and timing
   genogrove idx -k 5 -t genes.bed

   # Index pre-sorted data (faster insertion)
   genogrove idx -s sorted_genes.bed -o genes.gg

isec (Intersect)
~~~~~~~~~~~~~~~~

The ``isec`` subcommand finds overlapping intervals between a query file and a target file.

**Usage:**

.. code-block:: bash

   genogrove isec -q <queryfile> -t <targetfile> [OPTIONS]

**Options:**

.. list-table::
   :widths: 25 55 20
   :header-rows: 1

   * - Option
     - Description
     - Default
   * - ``-q, --queryfile``
     - The query file containing intervals to search
     - (required)
   * - ``-t, --targetfile``
     - The target file to build the index from and search against
     - (required)
   * - ``-o, --outputfile``
     - Write results to the specified file
     - stdout
   * - ``-k, --order``
     - The order of the B+ tree
     - 3
   * - ``-h, --help``
     - Print help information
     -

**Example:**

.. code-block:: bash

   # Find overlaps between query regions and genes
   genogrove isec -q regions.bed -t genes.bed

   # Write results to a file
   genogrove isec -q regions.bed -t genes.bed -o overlaps.bed

   # Use a higher tree order for large datasets
   genogrove isec -q regions.bed -t genes.bed -k 5

**Output Format:**

The intersection results are output in BED format (tab-separated):

.. code-block:: text

   chromosome    start    end

Each line represents a target interval that overlaps with at least one query interval.

Supported File Formats
----------------------

Currently, the CLI supports:

- **BED** - Browser Extensible Data format (``.bed``, ``.bed.gz``)

Additional formats (GFF, GTF, VCF) are planned for future releases.

Examples
--------

**Basic intersection workflow:**

.. code-block:: bash

   # Find all genes that overlap with your regions of interest
   genogrove isec -q my_regions.bed -t reference_genes.bed -o overlapping_genes.bed

**Working with compressed files:**

.. code-block:: bash

   # Compressed files are automatically detected
   genogrove isec -q regions.bed.gz -t genes.bed.gz

**Performance tuning:**

The ``-k`` (order) parameter controls the B+ tree branching factor. Higher values can improve query performance for large datasets at the cost of more memory during index construction:

.. code-block:: bash

   # Use order 5 for large datasets
   genogrove isec -q regions.bed -t large_annotation.bed -k 5