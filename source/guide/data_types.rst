Working with Data Types
========================

The ``genogrove::data_type`` namespace provides core genomic data types.

Common Interface
----------------

All data types implement a common set of functions:

- Comparison operators: ``<``, ``>``, ``==``
- ``overlap(a, b)`` - Static method to check if two values overlap
- ``aggregate(values)`` - Combine multiple values into one (e.g., bounding interval, maximum value)
- ``to_string()`` - String representation
- ``serialize(os)`` - Write binary representation to an output stream
- ``deserialize(is)`` - Static method to reconstruct a value from an input stream

The semantics of ``overlap()`` and ``aggregate()`` vary by type, as described in each section below.

Intervals
---------

The ``interval`` class represents genomic regions using 0-based, closed coordinates:

.. code-block:: cpp

   #include <genogrove/data_type/interval.hpp>

   namespace gdt = genogrove::data_type;

   int main() {
       // 1. Create intervals
       gdt::interval iv1{100, 200};  // [100, 200]
       gdt::interval iv2{150, 250};  // [150, 250]
       gdt::interval iv3{50, 75};    // [50, 75]

       // 2. Comparison operators (sorted by start, then by end)
       iv3 < iv1;   // true: 50 < 100
       iv1 < iv2;   // true: same start? no, 100 < 150
       iv1 == iv1;  // true: same start and end
       iv1 > iv3;   // true: 100 > 50

       // 3. Overlap - checks if ranges intersect
       gdt::interval::overlap(iv1, iv2);  // true: [100,200] and [150,250] intersect
       gdt::interval::overlap(iv1, iv3);  // false: [100,200] and [50,75] don't intersect

       // 4. Aggregate - returns bounding interval
       std::vector<gdt::interval> intervals = {iv1, iv2, iv3};
       auto bounds = gdt::interval::aggregate(intervals);  // [50, 250]

       // 5. String representation
       iv1.to_string();  // "[100, 200]"

       // 6. Serialization
       std::ostringstream oss(std::ios::binary);
       iv1.serialize(oss);

       // 7. Deserialization
       std::istringstream iss(oss.str(), std::ios::binary);
       auto iv_restored = gdt::interval::deserialize(iss);  // [100, 200]

       return 0;
   }

**Interval Semantics:**

- Comparison: Sorted by start position first, then by end position
- Overlap: Two intervals overlap if their ranges intersect
- Aggregate: Returns the bounding interval (minimum start, maximum end)
- Additional accessors: ``get_start()``, ``set_start()``, ``get_end()``, ``set_end()``
- Serialization: ``serialize(os)``, ``deserialize(is)``

Genomic Coordinates
-------------------

The ``genomic_coordinate`` class extends intervals with strand information:

.. code-block:: cpp

   #include <genogrove/data_type/genomic_coordinate.hpp>

   namespace gdt = genogrove::data_type;

   int main() {
       // 1. Create genomic coordinates (strand, start, end)
       gdt::genomic_coordinate gc1{'+', 100, 200};
       gdt::genomic_coordinate gc2{'+', 150, 250};
       gdt::genomic_coordinate gc3{'-', 100, 200};
       gdt::genomic_coordinate gc4{'*', 300, 400};  // wildcard strand; mainly used for queries

       // 2. Comparison operators (sorted by start, then end, then strand)
       // Strand order: * < . < + < -
       gc1 < gc3;   // true: same position, but + < -
       gc1 == gc1;  // true: same start, end, and strand
       gc1 < gc4;   // true: 100 < 300

       // 3. Overlap - requires both range intersection AND strand matching
       gdt::genomic_coordinate::overlap(gc1, gc2);  // true: same strand (+), ranges intersect
       gdt::genomic_coordinate::overlap(gc1, gc3);  // false: different strands (+ vs -)
       gdt::genomic_coordinate::overlap(gc4, gc1);  // true: wildcard * matches any strand

       // 4. Aggregate - returns bounding coordinate
       std::vector<gdt::genomic_coordinate> coords = {gc1, gc2};
       auto bounds = gdt::genomic_coordinate::aggregate(coords);  // {'+', 100, 250}

       // Mixed strands aggregate to wildcard
       std::vector<gdt::genomic_coordinate> mixed = {gc1, gc3};
       auto mixed_bounds = gdt::genomic_coordinate::aggregate(mixed);  // {'*', 100, 200}

       // 5. String representation
       gc1.to_string();  // "+:100-200"

       // 6. Serialization
       std::ostringstream oss(std::ios::binary);
       gc1.serialize(oss);

       // 7. Deserialization
       std::istringstream iss(oss.str(), std::ios::binary);
       auto gc_restored = gdt::genomic_coordinate::deserialize(iss);  // {'+', 100, 200}

       return 0;
   }

**Genomic Coordinate Semantics:**

- Comparison: Sorted by start, then end, then strand (strand order: ``*`` < ``.`` < ``+`` < ``-``)
- Overlap: Requires both range intersection AND strand matching. Use wildcard ``*`` to match any strand.
- Aggregate: Returns bounding coordinate; uses wildcard ``*`` strand when aggregating mixed strands
- Additional accessors: ``get_strand()``, ``set_strand()``, ``get_start()``, ``set_start()``, ``get_end()``, ``set_end()``
- Serialization: ``serialize(os)``, ``deserialize(is)``

Numeric
-------

The ``numeric`` class provides a simple integer wrapper for basic B+ tree operations with point-based semantics:

.. code-block:: cpp

   #include <genogrove/data_type/numeric.hpp>

   namespace gdt = genogrove::data_type;

   int main() {
       // 1. Create numeric values
       gdt::numeric n1{42};
       gdt::numeric n2{100};
       gdt::numeric n3{42};

       // 2. Comparison operators (standard integer comparison)
       n1 < n2;   // true: 42 < 100
       n1 == n3;  // true: 42 == 42
       n2 > n1;   // true: 100 > 42

       // 3. Overlap - only when values are exactly equal
       gdt::numeric::overlap(n1, n3);  // true: both are 42
       gdt::numeric::overlap(n1, n2);  // false: 42 != 100

       // 4. Aggregate - returns the maximum value
       std::vector<gdt::numeric> nums = {n1, n2, n3};
       auto max_val = gdt::numeric::aggregate(nums);  // 100

       // 5. String representation
       n1.to_string();  // "42"

       // 6. Serialization
       std::ostringstream oss(std::ios::binary);
       n1.serialize(oss);

       // 7. Deserialization
       std::istringstream iss(oss.str(), std::ios::binary);
       auto n_restored = gdt::numeric::deserialize(iss);  // 42

       return 0;
   }

**Numeric Semantics:**

- Comparison: Standard integer comparison
- Overlap: Two numeric values overlap only when exactly equal
- Aggregate: Returns the maximum value
- Additional accessors: ``get_value()``, ``set_value()``
- Serialization: ``serialize(os)``, ``deserialize(is)``
- Demonstrates that grove works as a standard B+ tree for non-interval data

K-mer
-----

The ``kmer`` class represents DNA subsequences using compact 2-bit encoding (A=00, C=01, G=10, T=11):

.. code-block:: cpp

   #include <genogrove/data_type/kmer.hpp>

   namespace gdt = genogrove::data_type;

   int main() {
       // 1. Create k-mers (case-insensitive, up to length 32)
       gdt::kmer k1{"ACGT"};
       gdt::kmer k2{"acgt"};  // Same as k1
       gdt::kmer k3{"TGCA"};
       gdt::kmer k4{"ACGTAA"};  // Different k (6 vs 4)

       // 2. Comparison operators (sorted by k value first, then by encoding)
       k1 == k2;  // true: same sequence (case-insensitive)
       k1 < k3;   // true: "ACGT" encoding < "TGCA" encoding
       k1 < k4;   // true: k=4 < k=6

       // 3. Overlap - only when k-mers are exactly equal
       gdt::kmer::overlap(k1, k2);  // true: same k-mer
       gdt::kmer::overlap(k1, k3);  // false: different sequences
       gdt::kmer::overlap(k1, k4);  // false: different k values

       // 4. Aggregate - returns the maximum encoding
       std::vector<gdt::kmer> kmers = {k1, k3};
       auto max_kmer = gdt::kmer::aggregate(kmers);  // "TGCA" (higher encoding)

       // 5. String representation
       k1.to_string();  // "ACGT"

       // 6. Serialization
       std::ostringstream oss(std::ios::binary);
       k1.serialize(oss);

       // 7. Deserialization
       std::istringstream iss(oss.str(), std::ios::binary);
       auto k_restored = gdt::kmer::deserialize(iss);  // "ACGT"

       return 0;
   }

**K-mer Semantics:**

- Comparison: Sorted by k value first, then by 2-bit encoding
- Overlap: Two k-mers overlap only when exactly equal (same k and same sequence)
- Aggregate: Returns the k-mer with maximum encoding
- Supports k-mers up to length 32 (stored in ``uint64_t``)
- Serialization: ``serialize(os)``, ``deserialize(is)``

**Helper Functions:**

The k-mer class provides static helper functions for working with nucleotide encoding:

.. code-block:: cpp

   #include <genogrove/data_type/kmer.hpp>

   namespace gdt = genogrove::data_type;

   int main() {
       // 1. Validate a DNA sequence before creating a k-mer
       std::string seq1 = "ACGT";
       std::string seq2 = "ACGN";  // Contains invalid 'N'

       gdt::kmer::is_valid(seq1);  // true: only A, C, G, T
       gdt::kmer::is_valid(seq2);  // false: 'N' is not valid

       // 2. Encode a single nucleotide to its 2-bit representation
       gdt::kmer::encode_base('A');  // 0 (binary: 00)
       gdt::kmer::encode_base('C');  // 1 (binary: 01)
       gdt::kmer::encode_base('G');  // 2 (binary: 10)
       gdt::kmer::encode_base('T');  // 3 (binary: 11)
       gdt::kmer::encode_base('a');  // 0 (case-insensitive)

       // 3. Decode a 2-bit value back to a nucleotide character
       gdt::kmer::decode_base(0);  // 'A'
       gdt::kmer::decode_base(1);  // 'C'
       gdt::kmer::decode_base(2);  // 'G'
       gdt::kmer::decode_base(3);  // 'T'

       return 0;
   }

- ``is_valid(sequence)``: Check if a string contains only valid nucleotides (A, C, G, T - case insensitive)
- ``encode_base(base)``: Convert a nucleotide character to its 2-bit encoding (throws ``std::invalid_argument`` for invalid characters)
- ``decode_base(encoding)``: Convert a 2-bit value (0-3) back to the nucleotide character

.. toctree::
   :maxdepth: 1

   data_types/key
   data_types/data_registry