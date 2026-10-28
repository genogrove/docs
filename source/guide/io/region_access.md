# Region Access

The BED, GFF and VCF readers can read **only the records overlapping one locus** instead of
streaming the whole file. Pass a region string in tabix form (`"chrom:start-end"`) and the reader
seeks through the file's index — a companion file (`.tbi` / `.csi`) that records where each
chromosome's blocks sit; iteration, record types and the error contract are otherwise unchanged. A
per-locus lookup costs in proportion to the records in the region, not the size of the file
({term}`O(records in the region) <O(log n), O(n)>`, not O(file)).

## Querying a region

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

```cpp
#include <genogrove/io/bed_reader.hpp>
#include <genogrove/io/gff_reader.hpp>
#include <genogrove/io/vcf_reader.hpp>
#include <iostream>

namespace gio = genogrove::io;

int main() {
    // Only records overlapping the EGFR locus; {.region = ...} sets that one option
    gio::gff_reader genes("genes.gff3.gz", {.region = "chr7:55000000-55300000"});
    for (const auto& e : genes) {
        std::cout << e.type << " " << e.start << "-" << e.end << "\n";
    }

    // Same option on the other two readers
    gio::bed_reader peaks("peaks.bed.gz", {.region = "chr1:1-1000000"});
    gio::vcf_reader calls("calls.vcf.gz", {.region = "chr1:1-1000000"});
    for (const auto& p : peaks) std::cout << p.chrom << ":" << p.start << "-" << p.end << "\n";
    for (const auto& v : calls) std::cout << v.chrom << ":" << v.start << " " << v.ref << "\n";
    return 0;
}
```

An empty `region` (the default) streams the whole file.

::::

::::{tab-item} {{ py_tab }}
:sync: py

```python
import pygenogrove as pg

# Only records overlapping the EGFR locus
for e in pg.GffReader("genes.gff3.gz", region="chr7:55000000-55300000"):
    print(e.type, e.start, e.end)

# Same option on the other two readers
for p in pg.BedReader("peaks.bed.gz", region="chr1:1-1000000"):
    print(p.chrom, p.start, p.end)
for v in pg.VcfReader("calls.vcf.gz", region="chr1:1-1000000"):
    print(v.chrom, v.start, v.ref)
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
bgzip and must be prepared first.

The tools for that come with the same libraries genogrove uses: `bgzip` and `tabix` ship with
[htslib](https://www.htslib.org/) (`conda install -c bioconda htslib`, `apt install tabix`, or
`brew install htslib`), and `bcftools` is the companion package for VCF/BCF
(`conda install -c bioconda bcftools`, `apt install bcftools`, `brew install bcftools`). Both
indexers require the records to be **sorted** by sequence name and then start position, so sort
before compressing:

```bash
# BED: sort, block-compress, index
sort -k1,1 -k2,2n peaks.bed | bgzip > peaks.bed.gz
tabix -p bed peaks.bed.gz                                    # writes peaks.bed.gz.tbi

# GFF / GTF: same, dropping the comment lines first
zcat annotations.gff3.gz | grep -v '^#' | sort -k1,1 -k4,4n | bgzip > annotations.sorted.gff3.gz
tabix -p gff annotations.sorted.gff3.gz                      # writes .tbi

# VCF: bcftools sorts and compresses in one step, then index
bcftools sort calls.vcf -Oz -o calls.vcf.gz
tabix -p vcf calls.vcf.gz                                    # writes .tbi (tabix -C for .csi)

# BCF: sort, then index (always .csi)
bcftools sort calls.bcf -Ob -o calls.sorted.bcf
bcftools index calls.sorted.bcf
```

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

The failure is a `std::runtime_error` {term}`exception` from the constructor.

The region option is implemented on `gio::tabix_reader` (`<genogrove/io/bgzf_utils.hpp>`), a public
wrapper over htslib's tabix iterator that opens the index when constructed and closes it when
destroyed. It is usable on its own to stream the raw, newline-stripped lines overlapping a
locus from any tabix-indexed file, with the same index requirements and error behaviour; see the
{doc}`I/O reference </reference/cpp/io>`.

::::

::::{tab-item} {{ py_tab }}
:sync: py

The failure is a `RuntimeError` from the constructor. The underlying tabix iterator is not exposed
separately in Python.

::::

:::::
