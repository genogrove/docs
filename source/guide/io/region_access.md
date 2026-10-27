# Region Access

The BED, GFF and VCF readers can read **only the records overlapping one locus** instead of
streaming the whole file. Pass a tabix region string (`"chrom:start-end"`) and the reader seeks
through the file's index; iteration, record types and the error contract are otherwise unchanged.
A per-locus lookup is O(records in the region), not O(file).

## Querying a region

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

```cpp
#include <genogrove/io/gff_reader.hpp>

namespace gio = genogrove::io;

// Only records overlapping the EGFR locus
gio::gff_reader r("genes.gff3.gz", {.region = "chr7:55000000-55300000"});
for (const auto& e : r) { /* ... */ }

gio::bed_reader b("peaks.bed.gz", {.region = "chr1:1-1000000"});
gio::vcf_reader v("calls.vcf.gz", {.region = "chr1:1-1000000"});
```

An empty `region` (the default) streams the whole file.

::::

::::{tab-item} {{ py_tab }}
:sync: py

```python
import pygenogrove as pg

# Only records overlapping the EGFR locus
for e in pg.GffReader("genes.gff3.gz", region="chr7:55000000-55300000"):
    ...

for e in pg.BedReader("peaks.bed.gz", region="chr1:1-1000000"):
    ...
for v in pg.VcfReader("calls.vcf.gz", region="chr1:1-1000000"):
    ...
```

An empty `region=""` (the default) streams the whole file.

::::

:::::

## Region coordinates

The region string uses **tabix query coordinates: 1-based, closed** — regardless of the reader's
native convention. BED and VCF records are 0-based half-open and GFF records are 1-based closed,
but the query is always 1-based closed. To select a BED feature stored as 0-based `[1000, 2000)`,
ask for `chr1:1001-2000`.

## Index requirement

Region access needs a block-compressed, indexed input:

- **BED / GFF** — bgzip-compressed with a tabix index (`.tbi` or `.csi`)
- **VCF / BCF** — a CSI-indexed BCF, or a bgzip-compressed VCF with a `.tbi` / `.csi` index

A plain, plain-gzip or unindexed file, an invalid region, or an unknown sequence name fails at
construction. Files distributed as plain gzip (e.g. a downloaded GENCODE `.gff3.gz`) are **not**
bgzip and must be recompressed and indexed first:

```bash
# BED / GFF
bgzip annotations.gff3                 # -> annotations.gff3.gz (bgzip)
tabix -p gff annotations.gff3.gz       # -> annotations.gff3.gz.tbi

# VCF / BCF
bgzip calls.vcf && tabix -p vcf calls.vcf.gz   # .tbi (or tabix -C for .csi)
bcftools index calls.bcf                        # .csi for a BCF
```

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

The failure is a `std::runtime_error` from the constructor.

The region option is implemented on `gio::tabix_reader` (`<genogrove/io/bgzf_utils.hpp>`), a public
RAII wrapper over htslib's tabix iterator. It is usable on its own to stream the raw,
newline-stripped lines overlapping a locus from any tabix-indexed file, with the same index
requirements and error behaviour; see the {doc}`I/O reference </reference/cpp/io>`.

::::

::::{tab-item} {{ py_tab }}
:sync: py

The failure is a `RuntimeError` from the constructor. The underlying tabix iterator is not exposed
separately in Python.

::::

:::::