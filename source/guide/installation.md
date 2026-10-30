# Installation

This guide covers how to build and install genogrove for use in your projects.

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

This guide covers how to build and install genogrove for use in your projects.

### Prerequisites

Before building genogrove, ensure you have:

- **C++20 compatible compiler**
  \- GCC 13 or newer
  \- Clang 16 or newer
  \- Apple Clang 15 or newer
- **CMake 3.14 or higher**
- **htslib** (for compressed file support)
  \- On Ubuntu/Debian: `sudo apt-get install libhts-dev`
  \- On macOS with Homebrew: `brew install htslib`
  \- On other systems: Build from source at <https://github.com/samtools/htslib>

### Building from Source

1. Clone the repository:

   ```bash
   git clone https://github.com/genogrove/genogrove.git
   cd genogrove
   ```

2. Create a build directory and configure:

   ```bash
   cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
   cmake --build build
   ```

3. (Optional) Run tests:

   ```bash
   # Tests are built when -DBUILD_TESTING=ON
   cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=ON
   cmake --build build
   cd build
   ctest -C Release
   ```

### Using in Your Project

#### CMake Integration

If you're using CMake, add genogrove to your project:

**Option 1: Install system-wide**

```bash
# From the build directory
sudo cmake --install .
```

Then in your `CMakeLists.txt`:

```cmake
find_package(genogrove REQUIRED)

add_executable(my_program main.cpp)
target_link_libraries(my_program genogrove::genogrove)
```

**Option 2: Add as subdirectory**

```cmake
add_subdirectory(external/genogrove)

add_executable(my_program main.cpp)
target_link_libraries(my_program genogrove::genogrove)
```

**Option 3: Use FetchContent**

```cmake
include(FetchContent)

FetchContent_Declare(
    genogrove
    GIT_REPOSITORY https://github.com/genogrove/genogrove.git
    GIT_TAG main  # or specific version tag
)
FetchContent_MakeAvailable(genogrove)

add_executable(my_program main.cpp)
target_link_libraries(my_program genogrove::genogrove)
```

genogrove is a **compiled library**, not header-only: the headers under `include/` are backed by
`libgenogrove` (built from `src/`), which itself links htslib and zlib. The `genogrove::genogrove`
CMake target carries all of that, so with any of the three options above you only link that one
target.

#### Manual Integration

If not using CMake, point the compiler at the headers and link the built library plus its
dependencies:

```bash
# Example with g++ — adjust the two paths to your checkout / build directory
g++ -std=c++20 -I/path/to/genogrove/include main.cpp \
    -L/path/to/genogrove/build -lgenogrove -lhts -lz -lpthread -o my_program
```

- `-lgenogrove` — the library built in step 2 above (`build/libgenogrove.a` or `.so`)
- `-lhts`, `-lz` — htslib and zlib, which genogrove links publicly
- `-lpthread` — on Linux

### Verify Installation

Create a simple test program. It stores one named interval and finds it again with a query:

```cpp
#include <genogrove/structure/grove/grove.hpp>
#include <genogrove/data_type/interval.hpp>
#include <iostream>

namespace gdt = genogrove::data_type;
namespace gst = genogrove::structure;

int main() {
    gst::grove<gdt::interval, std::string> g(100);
    g.insert_data("chr1", gdt::interval{100, 200}, "FOO");

    auto hits = g.intersect(gdt::interval{150, 160}, "chr1");
    std::cout << hits.get_keys().size() << " " << hits.get_keys()[0]->get_data() << "\n";
    return 0;
}
```

Compile and run, using the same include path and libraries as in
[Manual Integration](#manual-integration) (or a two-line CMake project linking
`genogrove::genogrove`):

```bash
g++ -std=c++20 -I/path/to/genogrove/include test.cpp \
    -L/path/to/genogrove/build -lgenogrove -lhts -lz -lpthread -o test   # drop -lpthread on macOS
./test
# Output: 1 FOO
```

If the compiler reports `genogrove/data_type/interval.hpp: No such file or directory`, the `-I`
path is wrong; if the linker reports undefined references to `genogrove::` symbols, `-L` /
`-lgenogrove` is missing.

### Development Build

For development with debugging symbols and sanitizers:

```bash
cmake -S . -B build-debug \
    -DCMAKE_BUILD_TYPE=Debug \
    -DBUILD_TESTING=ON \
    -DENABLE_SANITIZER=ON
cmake --build build-debug
```

See `SANITIZERS.md` in the repository for more information on using AddressSanitizer and UndefinedBehaviorSanitizer.

### Troubleshooting

**htslib not found**

If CMake cannot find htslib:

```bash
# Specify htslib location manually
cmake -S . -B build -DHTSLIB_ROOT=/path/to/htslib
```

**C++20 features not available**

Ensure your compiler supports C++20:

```bash
# Check GCC version
g++ --version  # Should be 13+

# Check Clang version
clang++ --version  # Should be 16+
```

**Build fails on older systems**

Consider using a newer compiler via devtoolset (RHEL/CentOS) or a PPA (Ubuntu):

```bash
# Ubuntu example
sudo add-apt-repository ppa:ubuntu-toolchain-r/test
sudo apt update
sudo apt install gcc-13 g++-13
export CXX=g++-13
```

### Next Steps

Once installed, proceed to the next sections of the user guide to learn how to use genogrove effectively.

::::

::::{tab-item} {{ py_tab }}
:sync: py

### Install

```bash
pip install pygenogrove
```

Wheels are published for Python 3.10–3.14 (3.9 is end-of-life and no longer built) on Linux x86_64
(glibc, not musl) and Apple Silicon macOS 14+. A wheel bundles the genogrove C++ library and
htslib, so nothing else needs to be installed. On any other platform — Intel Mac, Windows, aarch64
or musl Linux — `pip install pygenogrove` builds from the source distribution, which requires a
C++20 compiler, CMake 3.15+ (the pygenogrove build; the C++ library alone needs 3.14), htslib, and
Python 3.10+; the same applies to building a checkout by hand:

```bash
git clone --recursive https://github.com/genogrove/pygenogrove.git
cd pygenogrove
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build
```

### Verify Installation

```python
import pygenogrove as pg

g = pg.Grove(100)
g.insert("chr1", pg.GenomicCoordinate("+", 100, 200), "FOO")

hits = list(g.intersect(pg.GenomicCoordinate("*", 150, 160), "chr1"))
print(len(hits), hits[0].data)      # 1 FOO
```

### Checking your version

`pygenogrove` exposes two module-level version attributes that move on independent cadences — the binding package versions its own surface, while `__genogrove_version__` advertises the bound C++ library. When filing a bug, report **both**:

```python
import pygenogrove as pg
print(pg.__version__)             # the pygenogrove package version, e.g. "0.10.0"
print(pg.__genogrove_version__)   # the genogrove C++ library it was built against, e.g. "0.27.0"
```

::::

:::::