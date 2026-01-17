Key
===

The ``key`` class is a wrapper that combines a key value (e.g., interval, genomic_coordinate, kmer) with optional associated data. It serves as the fundamental storage unit in grove structures, enabling efficient indexing while maintaining arbitrary metadata.

Template Parameters
-------------------

The key class takes two template parameters:

- ``key_type``: The core key value type (must satisfy ``key_type_base`` concept)
- ``data_type``: Optional associated data type (default: ``void`` for keys without data)

.. code-block:: cpp

   #include <genogrove/data_type/key.hpp>
   #include <genogrove/data_type/interval.hpp>

   namespace gdt = genogrove::data_type;

   // Key without data (data_type = void)
   gdt::key<gdt::interval> k1{gdt::interval{100, 200}};

   // Key with data
   struct GeneInfo {
       std::string name;
       double score;
   };
   gdt::key<gdt::interval, GeneInfo> k2{
       gdt::interval{100, 200},
       GeneInfo{"BRCA1", 0.95}
   };

Basic Usage
-----------

.. code-block:: cpp

   #include <genogrove/data_type/key.hpp>
   #include <genogrove/data_type/interval.hpp>

   namespace gdt = genogrove::data_type;

   struct GeneInfo {
       std::string name;
       double expression;
   };

   int main() {
       // 1. Create a key with value and data
       gdt::key<gdt::interval, GeneInfo> gene_key{
           gdt::interval{100, 200},
           GeneInfo{"BRCA1", 45.3}
       };

       // 2. Access the key value
       const auto& interval = gene_key.get_value();
       std::cout << interval.to_string() << "\n";  // "[100, 200]"

       // 3. Access associated data (const)
       const auto& info = gene_key.get_data();
       std::cout << info.name << "\n";  // "BRCA1"

       // 4. Modify data in place (mutable access)
       gene_key.get_data().expression = 50.0;

       // 5. Replace data entirely
       gene_key.set_data(GeneInfo{"TP53", 32.1});

       // 6. Replace the key value
       gene_key.set_value(gdt::interval{300, 400});

       // 7. Check if key has data (compile-time constant)
       if (gene_key.has_data()) {
           std::cout << "Key has associated data\n";
       }

       // 8. String representation (delegates to key_type)
       std::cout << gene_key.to_string() << "\n";  // "[300, 400]"

       return 0;
   }

Keys Without Data
-----------------

When ``data_type`` is ``void``, the key contains only the value with zero memory overhead:

.. code-block:: cpp

   #include <genogrove/data_type/key.hpp>
   #include <genogrove/data_type/interval.hpp>

   namespace gdt = genogrove::data_type;

   int main() {
       // Key without data - just the interval
       gdt::key<gdt::interval> simple_key{gdt::interval{100, 200}};

       // Access value works the same way
       const auto& interval = simple_key.get_value();

       // has_data() returns false (compile-time)
       static_assert(!gdt::key<gdt::interval>::has_data());

       // get_data() and set_data() do not compile - disabled at compile time
       // simple_key.get_data();  // Error: method doesn't exist

       return 0;
   }

Comparison Operators
--------------------

Keys support equality comparison:

.. code-block:: cpp

   #include <genogrove/data_type/key.hpp>
   #include <genogrove/data_type/interval.hpp>

   namespace gdt = genogrove::data_type;

   int main() {
       // Keys without data: compare only values
       gdt::key<gdt::interval> k1{gdt::interval{100, 200}};
       gdt::key<gdt::interval> k2{gdt::interval{100, 200}};
       gdt::key<gdt::interval> k3{gdt::interval{100, 300}};

       k1 == k2;  // true: same interval
       k1 == k3;  // false: different end
       k1 != k3;  // true

       // Keys with data: compare both value AND data
       gdt::key<gdt::interval, std::string> kd1{gdt::interval{100, 200}, "gene1"};
       gdt::key<gdt::interval, std::string> kd2{gdt::interval{100, 200}, "gene1"};
       gdt::key<gdt::interval, std::string> kd3{gdt::interval{100, 200}, "gene2"};

       kd1 == kd2;  // true: same interval AND same data
       kd1 == kd3;  // false: same interval but different data

       return 0;
   }

Serialization
-------------

Keys support binary serialization for persistence:

.. code-block:: cpp

   #include <genogrove/data_type/key.hpp>
   #include <genogrove/data_type/interval.hpp>
   #include <sstream>

   namespace gdt = genogrove::data_type;

   int main() {
       gdt::key<gdt::interval, std::string> original{
           gdt::interval{100, 200},
           "gene1"
       };

       // Serialize to binary stream
       std::ostringstream oss(std::ios::binary);
       original.serialize(oss);

       // Deserialize from binary stream
       std::istringstream iss(oss.str(), std::ios::binary);
       auto restored = gdt::key<gdt::interval, std::string>::deserialize(iss);

       // restored == original
       std::cout << restored.get_value().to_string() << "\n";  // "[100, 200]"
       std::cout << restored.get_data() << "\n";               // "gene1"

       return 0;
   }

Using Keys with Grove
---------------------

The key class is the internal storage type used by grove. When you insert data into a grove, it creates keys internally:

.. code-block:: cpp

   #include <genogrove/structure/grove/grove.hpp>
   #include <genogrove/data_type/interval.hpp>

   namespace gdt = genogrove::data_type;
   namespace gst = genogrove::structure;

   int main() {
       // Grove stores key<interval, std::string> internally
       gst::grove<gdt::interval, std::string> my_grove(100);

       // insert_data returns a pointer to the internal key
       auto* key_ptr = my_grove.insert_data("chr1",
                                            gdt::interval{100, 200},
                                            "gene1");

       // Access via key pointer
       std::cout << key_ptr->get_value().to_string() << "\n";  // "[100, 200]"
       std::cout << key_ptr->get_data() << "\n";               // "gene1"

       // Query results return key pointers
       auto results = my_grove.intersect(gdt::interval{150, 175}, "chr1");
       for (auto* k : results.get_keys()) {
           std::cout << k->get_value().to_string() << ": "
                     << k->get_data() << "\n";
       }

       return 0;
   }

Memory Optimization
-------------------

The key class uses several C++ techniques to minimize memory overhead:

- **Zero-overhead for void data**: When ``data_type`` is ``void``, the key stores ``std::monostate`` with ``[[no_unique_address]]``, resulting in zero additional memory
- **Move semantics**: Constructors and setters use move semantics to avoid unnecessary copies
- **Compile-time method elimination**: Methods like ``get_data()`` don't exist when ``data_type`` is ``void`` (using ``requires`` clauses)

.. code-block:: cpp

   #include <genogrove/data_type/key.hpp>
   #include <genogrove/data_type/interval.hpp>

   namespace gdt = genogrove::data_type;

   // Key without data has same size as interval alone
   static_assert(sizeof(gdt::key<gdt::interval>) == sizeof(gdt::interval));

   // Key with data adds only the data size
   static_assert(sizeof(gdt::key<gdt::interval, int>) ==
                 sizeof(gdt::interval) + sizeof(int));

**Key Features Summary:**

- ``get_value()``, ``set_value()``: Access/modify the key value
- ``get_data()``, ``set_data()``: Access/modify associated data (only when ``data_type != void``)
- ``has_data()``: Compile-time check for data presence
- ``to_string()``: String representation (delegates to key_type)
- ``serialize(os)``, ``deserialize(is)``: Binary persistence
- ``operator==``, ``operator!=``: Equality comparison