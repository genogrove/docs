# Custom Key Types

The grove sorts, searches and merges keys through a small, fixed set of operations. Any type that
provides them can be used as a {term}`key type`. This is a C++ feature; the Python bindings ship a
fixed set of key types.

## The `key_type_base` concept

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

A key type must satisfy the `key_type_base` concept (`<genogrove/data_type/key_type_base.hpp>`).
A C++ *concept* is a compile-time checklist of operations a type must provide; this one requires six
(the three comparison operators count separately):

1. Comparison operators `<`, `>`, `==`
2. A static {term}`overlap` test `overlaps(a, b) -> bool` (*static*: called on the type itself,
   `T::overlaps(a, b)`, not on a value)
3. A static pairwise aggregation `aggregate(a, b) -> T` (the bounding "box" of two keys, used for
   the tree's internal separator keys)
4. A string representation `to_string() -> std::string`

```cpp
#include <genogrove/data_type/key_type_base.hpp>
#include <genogrove/structure/grove/grove.hpp>
#include <algorithm>
#include <string>

namespace gdt = genogrove::data_type;
namespace gst = genogrove::structure;

struct CustomInterval {
    size_t start;
    size_t end;
    int priority;

    // operator< is how C++ spells "a < b" for your own type; the trailing const promises
    // that comparing does not change the object
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

int main() {
    // Use it like any built-in key type
    gst::grove<CustomInterval, std::string> my_grove(100);
    my_grove.insert_data("chr1", CustomInterval{100, 200, 1}, "gene1");
    return 0;
}
```

`grove` and `node` constrain their first {term}`template` parameter with the concept directly
(`template <gdt::key_type_base key_type, ...>`), so a type missing one of the six operations fails
to compile at your `grove<my_type>` line: the compiler reports that the constraints of `grove` are not
satisfied and names `key_type_base` and the missing requirement (e.g. `T::aggregate(a, b)`).

::::

::::{tab-item} {{ py_tab }}
:sync: py

Already covered: {term}`pygenogrove`'s groves ship the three key types most uses need — `GenomicCoordinate`
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
`std::hash<CustomInterval>` of your own (a small function object that turns a value into a
{term}`hash` number; C++ calls providing it for your type a *specialization*) only if you put the type in a {term}`registry` (whose `registry_value` concept
requires it) or in an unordered container such as `std::unordered_set`. Of the built-in types,
`genomic_coordinate`, `numeric` and `kmer` ship one; `interval` does not.

To save a grove keyed by your type to a file ({term}`serialization`), the type additionally needs a
`serialize(std::ostream&) const` member and a static `deserialize(std::istream&)` factory — a
function that builds a value from a {term}`stream` — see the
{doc}`serialization guide </guide/serialization/index>`. Write each field inside `serialize` with a
fixed-width type: `int32_t` is always 4 bytes and `uint64_t` is always 8 bytes. `long` and `wchar_t`
change width between platforms, so a file that holds them reads wrongly on another platform. The
"Portability across platforms" section of the serialization guide lists the rules.

::::

::::{tab-item} {{ py_tab }}
:sync: py

Already covered: the built-in `GenomicCoordinate`, `Numeric` and `Kmer` all hash by value (so they
work as `set` members and `dict` keys) and are saved with the grove by `serialize` — see the
{doc}`serialization guide </guide/serialization/index>`.

::::

:::::