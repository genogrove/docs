# Installation

This guide covers how to build and install genogrove for use in your projects.

## Prerequisites

Before building genogrove, ensure you have:

- **C++20 compatible compiler**
  \- GCC 12 or newer
  \- Clang 14 or newer
  \- MSVC 2022 or newer
- **CMake 3.15 or higher**
- **htslib** (for compressed file support)
  \- On Ubuntu/Debian: `sudo apt-get install libhts-dev`
  \- On macOS with Homebrew: `brew install htslib`
  \- On other systems: Build from source at <https://github.com/samtools/htslib>

## Building from Source

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

## Using in Your Project

### CMake Integration

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

### Manual Integration

If not using CMake:

1. Add the include directory to your include path:

   ```bash
   # Example with g++
   g++ -std=c++20 -I/path/to/genogrove/include main.cpp -lhts -o my_program
   ```

2. Link against required libraries:
   \- htslib (`-lhts`)
   \- pthread (`-lpthread`) on Linux

## Verify Installation

Create a simple test program:

```cpp
#include <genogrove/data_type/interval.hpp>
#include <iostream>

namespace gdt = genogrove::data_type;

int main() {
    gdt::interval iv{100, 200};
    std::cout << "Genogrove is working! Interval: "
              << iv.to_string() << std::endl;
    return 0;
}
```

Compile and run:

```bash
g++ -std=c++20 test.cpp -o test
./test
# Output: Genogrove is working! Interval: [100, 200)
```

## Development Build

For development with debugging symbols and sanitizers:

```bash
cmake -S . -B build-debug \
    -DCMAKE_BUILD_TYPE=Debug \
    -DBUILD_TESTING=ON \
    -DENABLE_SANITIZERS=ON
cmake --build build-debug
```

See `SANITIZERS.md` in the repository for more information on using AddressSanitizer and UndefinedBehaviorSanitizer.

## Troubleshooting

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
g++ --version  # Should be 12+

# Check Clang version
clang++ --version  # Should be 14+
```

**Build fails on older systems**

Consider using a newer compiler via devtoolset (RHEL/CentOS) or a PPA (Ubuntu):

```bash
# Ubuntu example
sudo add-apt-repository ppa:ubuntu-toolchain-r/test
sudo apt update
sudo apt install gcc-12 g++-12
export CXX=g++-12
```

## Next Steps

Once installed, proceed to the next sections of the user guide to learn how to use genogrove effectively.
