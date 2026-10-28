# Custom Key Types

The grove sorts, searches and merges keys through a small, fixed set of operations. Any type that
provides them can be used as a key type. This is a C++ feature; the Python bindings ship a fixed
set of key types.

## The `key_type_base` concept

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

A key type must satisfy the `key_type_base` concept (`<genogrove/data_type/key_type_base.hpp>`),
which requires six operations:

1. Comparison operators `<`, `>`, `==`
2. A static overlap test `overlaps(a, b) -> bool`
3. A static pairwise aggregation `aggregate(a, b) -> T` (the bounding "box" of two keys, used for
   the tree's internal separator keys)
4. A string representation `to_string() -> std::string`

```cpp
#include <genogrove/data_type/key_type_base.hpp>
#include <algorithm>
#include <string>

struct CustomInterval {
    size_t start;
    size_t end;
    int priority;

    bool operator<(const CustomInterval& other) const { return start < other.start; }
    bool operator>(const CustomInterval& other) const { return start > other.start; }
    bool operator==(const CustomInterval& other) const {
        return start == other.start && end == other.end;
    }

    static bool overlaps(const CustomInterval& a, const CustomInterval& b) {
        return !(a.end <= b.start || b.end <= a.start);
    }

    static CustomInterval aggregate(const CustomInterval& a, const CustomInterval& b) {
        return {std::min(a.start, b.start), std::max(a.end, b.end), 0};
    }

    std::string to_string() const {
        return "[" + std::to_string(start) + ", " + std::to_string(end) + ") p=" +
               std::to_string(priority);
    }
};

// Use it like any built-in key type
gst::grove<CustomInterval, std::string> my_grove(100);
```

`grove` and `node` constrain their first template parameter with the concept directly
(`template <gdt::key_type_base key_type, ...>`), so a type missing one of the six operations fails
at your `grove<my_type>` line: the compiler reports that the constraints of `grove` are not
satisfied and names `key_type_base` and the missing requirement (e.g. `T::aggregate(a, b)`).

::::

::::{tab-item} {{ py_tab }}
:sync: py

Not available. pygenogrove's groves are instantiated for three key types — `GenomicCoordinate`
(`Grove`, `BedGrove`, `GffGrove`), `Numeric` (`NumericGrove`) and `Kmer` (`KmerGrove`) — see
{doc}`index`. A C++ grove built on a custom key type cannot be opened from Python, and a `.gg` it
writes is not readable by any pygenogrove class.

If you need a different notion of "key" in Python, map it onto one of the three: integer ids fit
`Numeric`, short sequences fit `Kmer`, and anything with a start and an end fits
`GenomicCoordinate` with strand `'.'`.

::::

:::::

## Hashing and persistence

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

`std::hash` is **not** part of `key_type_base` — the grove never hashes keys. You need a
`std::hash<CustomInterval>` specialization only if you put the type in a `registry` (whose
`registry_value` concept requires it) or in an unordered container. Of the built-in types,
`genomic_coordinate`, `numeric` and `kmer` ship one; `interval` does not.

To persist a grove keyed by your type, it additionally needs a `serialize(std::ostream&) const`
member and a static `deserialize(std::istream&)` factory — see the
{doc}`serialization guide </guide/serialization/index>`.

::::

::::{tab-item} {{ py_tab }}
:sync: py

Not applicable. The built-in `GenomicCoordinate`, `Numeric` and `Kmer` all hash by value (so they
work as `set` members and `dict` keys) and serialize with the grove.

::::

:::::