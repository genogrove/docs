# User Guide

This user guide provides comprehensive coverage of genogrove's functionality, from reading genomic files to building complex data structures and queries.

Every topic below is documented with side-by-side **C++** and **Python** tabs — pick a language once and the choice follows you across all pages.

:::{note}
The **C++** tabs document **genogrove {{ cpp_version }}** (the core library). The **Python** tabs document **pygenogrove {{ py_version }}** (the bindings), which version independently and may not yet expose every C++ feature. Each tab label shows the version it reflects.
:::

## Prerequisites

Before starting, ensure you have:

- Installed genogrove or pygenogrove (see {doc}`guide/installation`)
- For C++: a C++20 compatible compiler (GCC 13+, Clang 16+, Apple Clang 15+). For Python: Python 3.10–3.14 and `pip install pygenogrove`; the published wheels need no compiler or htslib (a source build does — see the installation page).
- Basic familiarity with genomic file formats (BED, GFF/GTF)

## Guide Contents

Start with {doc}`guide/installation` and {doc}`guide/grove/index` (create a grove, insert, query),
then {doc}`guide/grove/loading_data` to fill it from a file and {doc}`guide/graph/index` to link keys. {doc}`guide/examples` has complete
programs. The remaining pages are reference-style and can be read as needed.

```{toctree}
:maxdepth: 3

guide/installation
guide/grove/index
guide/graph/index
guide/examples
guide/io/index
guide/data_types
guide/serialization
guide/performance
guide/thread_safety
```

## Next Steps

- Explore the full {doc}`reference/index` for detailed API documentation
- Check the [examples directory](https://github.com/genogrove/genogrove/tree/main/examples) in the repository
- Ask questions on [GitHub Discussions](https://github.com/genogrove/genogrove/discussions)
