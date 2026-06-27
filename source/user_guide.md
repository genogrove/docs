# User Guide

This user guide provides comprehensive coverage of genogrove's functionality, from reading genomic files to building complex data structures and queries.

Every topic below is documented with side-by-side **C++** and **Python** tabs — pick a language once and the choice follows you across all pages.

:::{note}
The **C++** tabs document **genogrove {{ cpp_version }}** (the core library). The **Python** tabs document **pygenogrove {{ py_version }}** (the bindings), which version independently and may not yet expose every C++ feature. Each tab label shows the version it reflects.
:::

## Prerequisites

Before starting, ensure you have:

- Installed genogrove (see {doc}`index` for installation instructions)
- A C++20 compatible compiler (GCC 13+, Clang 16+, Apple Clang 15+)
- Basic familiarity with genomic file formats (BED, GFF/GTF)

## Guide Contents

```{toctree}
:maxdepth: 3

guide/installation
guide/io
guide/data_types
guide/grove/grove
guide/serialization
guide/examples
guide/performance
```

## Next Steps

- Explore the full {doc}`reference/index` for detailed API documentation
- Check the [examples directory](https://github.com/genogrove/genogrove/tree/main/examples) in the repository
- Learn about advanced features in the project wiki
- Join the community discussions on GitHub
