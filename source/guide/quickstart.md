# Quickstart

A complete first program in about twenty lines: create a {term}`grove`, store three genomic
intervals, ask which of them overlap a region, and print the answer. No input files are needed.
When it runs, continue with {doc}`grove/index` for what each call does.

## 1. Install

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

Build the library once from a checkout (details and the CMake route in {doc}`installation`):

```bash
git clone https://github.com/genogrove/genogrove.git
cd genogrove
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build
```

You need a C++20 compiler (GCC 13+, Clang 16+, Apple Clang 15+), htslib and zlib.

::::

::::{tab-item} {{ py_tab }}
:sync: py

```bash
pip install pygenogrove
```

Wheels are published for Python 3.10–3.14; no compiler or htslib is needed.

::::

:::::

## 2. Write the program

Three intervals on `chr1`, named `gene1` to `gene3`, and one question: which of them overlap
positions 150 to 350? Coordinates are {term}`0-based closed`, so `[100, 200]` covers bases 100
through 200.

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

Save as `first_grove.cpp`:

```cpp
#include <genogrove/structure/grove/grove.hpp>
#include <genogrove/data_type/interval.hpp>
#include <iostream>

namespace gdt = genogrove::data_type;
namespace gst = genogrove::structure;

int main() {
    // A grove of intervals, each carrying a name. 100 is the tree order (a good default).
    gst::grove<gdt::interval, std::string> features(100);

    // insert_data(index, interval, payload): the index is the chromosome
    features.insert_data("chr1", gdt::interval{100, 200}, "gene1");
    features.insert_data("chr1", gdt::interval{300, 400}, "gene2");
    features.insert_data("chr1", gdt::interval{500, 600}, "gene3");

    // Which stored intervals overlap [150, 350] on chr1?
    auto results = features.intersect(gdt::interval{150, 350}, "chr1");

    for (const auto* key : results.get_keys()) {
        std::cout << key->get_value().to_string() << " " << key->get_data() << "\n";
    }
    return 0;
}
```

`insert_data` returns a handle to the stored key, which this program does not need. `intersect`
returns a `query_result`; `get_keys()` gives the matching keys as pointers, and each key has the
interval (`get_value()`) and the payload (`get_data()`).

::::

::::{tab-item} {{ py_tab }}
:sync: py

Save as `first_grove.py`:

```python
import pygenogrove as pg

# A grove whose keys are stranded coordinates and whose payloads are any JSON value.
# 100 is the tree order (a good default).
features = pg.Grove(100)

# insert(index, coordinate, payload): the index is the chromosome, "+" the strand
features.insert("chr1", pg.GenomicCoordinate("+", 100, 200), {"name": "gene1"})
features.insert("chr1", pg.GenomicCoordinate("+", 300, 400), {"name": "gene2"})
features.insert("chr1", pg.GenomicCoordinate("+", 500, 600), {"name": "gene3"})

# Which stored coordinates overlap [150, 350] on chr1? "*" means any strand.
results = features.intersect(pg.GenomicCoordinate("*", 150, 350), "chr1")

for key in results:
    print(key.value.start, key.value.end, key.data["name"])
```

`insert` returns a `Key` handle, which this program does not need. `intersect` returns a
{term}`QueryResult`: loop over it, and each `Key` has the coordinate (`.value`) and the payload
(`.data`).

::::

:::::

## 3. Run it

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

Point the compiler at the headers and the built library (adjust the two paths to your checkout;
drop `-lpthread` on macOS):

```bash
g++ -std=c++20 -I/path/to/genogrove/include first_grove.cpp \
    -L/path/to/genogrove/build -lgenogrove -lhts -lz -lpthread -o first_grove
./first_grove
```

Expected output:

```text
[100,200] gene1
[300,400] gene2
```

`gene3` at `[500, 600]` does not overlap `[150, 350]`, so it is not reported. If the compiler
cannot find `genogrove/structure/grove/grove.hpp`, the `-I` path is wrong; if the linker reports
undefined `genogrove::` symbols, `-L` / `-lgenogrove` is missing. A CMake project links
`genogrove::genogrove` instead — see {doc}`installation`.

::::

::::{tab-item} {{ py_tab }}
:sync: py

```bash
python first_grove.py
```

Expected output:

```text
100 200 gene1
300 400 gene2
```

`gene3` at `[500, 600]` does not overlap `[150, 350]`, so it is not reported.

::::

:::::

## Where next

- {doc}`grove/index` — what a grove stores, the tree order, indices and key handles; then
  {doc}`grove/inserting` and {doc}`grove/querying` for every form of insert and query.
- {doc}`grove/loading_data` — fill a grove from a BED, GFF/GTF or BAM file instead of by hand.
- {doc}`graph/index` — link keys with directed edges.
- {doc}`serialization/index` — save a grove to disk and load it back.
- {doc}`examples` — complete programs.
- {doc}`glossary` — every term the guide uses.
