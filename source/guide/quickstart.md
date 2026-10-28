# Quickstart

A complete first program in about twenty lines: create a {term}`grove`, store three genomic
intervals, ask which of them overlap a region, and print the answer. No input files are needed.
When it runs, continue with {doc}`grove/index` for what each call does.

## 1. Install

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

You need `git`, CMake 3.14+, `pkg-config`, a C++20 compiler (GCC 13+, Clang 16+, Apple Clang
15+), and the htslib and zlib libraries (`sudo apt-get install libhts-dev` on Ubuntu/Debian,
`brew install htslib` on macOS — see the [prerequisites](installation.md#prerequisites)). Then
build the library once from the source code:

```bash
git clone https://github.com/genogrove/genogrove.git
cd genogrove
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build
```

{doc}`installation` has the details and how to use the library from a CMake project.

::::

::::{tab-item} {{ py_tab }}
:sync: py

```bash
pip install pygenogrove       # pip3 on systems where "pip" is Python 2 or missing
```

Prebuilt packages are published for Python 3.10–3.14 on Linux x86_64 (glibc) and Apple Silicon
macOS 14+; there, nothing else needs to be installed. On other platforms (Intel Mac, Windows,
aarch64 or musl Linux) `pip` builds from source and needs the C++ prerequisites of the C++ tab —
see [the Python install section](installation.md#install).

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

The first argument of `insert_data` and the last of `intersect` is the {term}`index` — the
chromosome. `insert_data` returns a {term}`key handle <key>`, which this program does not need.
`intersect` returns a `query_result` (the C++ form of a {term}`QueryResult`); `get_keys()` gives
the matching keys, and each key has the interval (`get_value()`) and the payload (`get_data()`).

::::

::::{tab-item} {{ py_tab }}
:sync: py

Save as `first_grove.py`:

```python
import pygenogrove as pg

# A grove whose keys are coordinates with a strand and whose payloads can be a name,
# a number, or a dictionary like the ones below. 100 is the tree order (a good default).
features = pg.Grove(100)

# insert(index, coordinate, payload): the index is the chromosome, "+" the strand
features.insert("chr1", pg.GenomicCoordinate("+", 100, 200), {"name": "gene1"})
features.insert("chr1", pg.GenomicCoordinate("+", 300, 400), {"name": "gene2"})
features.insert("chr1", pg.GenomicCoordinate("+", 500, 600), {"name": "gene3"})

# Which stored coordinates overlap [150, 350] on chr1? "*" means any strand.
results = features.intersect(pg.GenomicCoordinate("*", 150, 350), "chr1")

for key in results:
    print(f"[{key.value.start},{key.value.end}] {key.data['name']}")
```

The first argument of `insert` and the last of `intersect` is the {term}`index` — the chromosome.
C++ stores the name itself; Python stores it as a JSON value, so the example wraps it in a dict.
Unlike the C++ `interval`, a Python coordinate always carries a {term}`strand`: the inserts use
`"+"`, and the query uses the wildcard `"*"` so it matches features on either strand. `insert`
returns a {term}`Key handle <key>`, which this program does not need. `intersect` returns a
{term}`QueryResult`: loop over it, and each `Key` has the coordinate (`.value`) and the payload
(`.data`).

::::

:::::

## 3. Run it

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

Point the compiler at the headers and the built library. Replace `/path/to/genogrove` with the
`genogrove` folder that `git clone` created in step 1; drop `-lpthread` on macOS (`g++` works
there too — it is Clang under another name):

```bash
g++ -std=c++20 -I/path/to/genogrove/include first_grove.cpp \
    -L/path/to/genogrove/build -lgenogrove -lhts -lz -lpthread -o first_grove
./first_grove
```

If htslib came from Homebrew, add `-I$(brew --prefix)/include -L$(brew --prefix)/lib` so `-lhts`
is found.

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
python first_grove.py         # python3 on systems where "python" is Python 2 or missing
```

Expected output:

```text
[100,200] gene1
[300,400] gene2
```

`gene3` at `[500, 600]` does not overlap `[150, 350]`, so it is not reported. If you see
`ModuleNotFoundError: No module named 'pygenogrove'`, the `pip` and `python` commands belong to
different Python installations; run `python -m pip install pygenogrove` with the same `python`.

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
