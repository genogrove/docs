# VCF / BCF Files

VCF and BCF files hold variant calls. One reader handles plain VCF, bgzipped VCF and binary BCF
(htslib detects which). Coordinates are **0-based half-open**: `start = POS - 1` and
`end = start + len(REF)`, so a SNP spans one base. Convert with `end - 1` for a grove key — the
BED/BAM rule, not the GFF one.

## Reading variants

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

```cpp
#include <genogrove/io/vcf_reader.hpp>
#include <iostream>

namespace gio = genogrove::io;

int main() {
    gio::vcf_reader reader("calls.vcf.gz");

    try {
        for (const auto& v : reader) {
            std::cout << v.chrom << ":" << v.start << "-" << v.end << " REF=" << v.ref;
            if (!v.qual_missing) std::cout << " QUAL=" << v.qual;
            if (v.is_snp())        std::cout << " SNP";
            else if (v.is_indel()) std::cout << " indel";
            for (const auto& s : v.samples) std::cout << " " << s.gt_string();
            std::cout << "\n";
        }
    } catch (const std::runtime_error& e) {
        std::cerr << "Read error: " << e.what() << "\n";
    }
    return 0;
}
```

```cpp
vcf_reader(const std::string& path, vcf_reader_options options = {});
struct vcf_reader_options {
    bool parse_info    = true;    // populate the typed INFO map
    bool parse_samples = true;    // decode per-sample FORMAT data
    bool skip_filtered = false;   // drop records that did not pass FILTER
    std::string region = "";      // tabix/CSI region, see region_access
};
// presets: vcf_reader_options::defaults(), vcf_reader_options::sites_only()
```

::::

::::{tab-item} {{ py_tab }}
:sync: py

```python
import pygenogrove as pg

for v in pg.VcfReader("calls.vcf.gz"):
    kind = "SNP" if v.is_snp() else "indel" if v.is_indel() else ""
    print(v.chrom, v.start, v.end, v.ref, v.alt, kind, [s.gt_string() for s in v.samples])
```

```python
VcfReader(path, parse_info=True, parse_samples=True, skip_filtered=False, region="")
```

::::

:::::

## The variant record

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

`gio::vcf_entry`:

| Field | Type |
|---|---|
| `chrom` | `std::string` |
| `start`, `end` | `size_t`, 0-based half-open (`POS - 1`, `start + len(REF)`) |
| `id` | `std::string`, empty for `.` |
| `ref` | `std::string` |
| `alt` | `std::vector<std::string>`; empty for `ALT=.`; symbolic alleles (`<*>`, `<NON_REF>`, `*`) kept verbatim |
| `qual`, `qual_missing` | `float`, and `true` when QUAL is `.` |
| `filter` | `std::vector<std::string>`; `{"PASS"}` when passed, empty for `.` |
| `info` | `vcf_info` = `std::unordered_map<std::string, vcf_info_value>`; the value is a `std::variant<bool, std::vector<int32_t>, std::vector<float>, std::string>` (Flag, Integer, Float, String — numeric fields are always vectors, even single values) |
| `format` | `std::vector<std::string>` FORMAT keys in column order |
| `samples` | `std::vector<sample_genotype>`, parallel to `get_sample_names()` |

Methods:

- `passed_filter()` — `true` if FILTER is `PASS` or `.`
- `is_snp()` — single-base REF and a single-base ALT
- `is_indel()` — insertion or deletion
- `static is_symbolic_allele(allele)` — `true` for `<*>`, `<NON_REF>`, `*`; such alleles are
  excluded from `is_snp()` / `is_indel()`

There is no coordinate helper on the C++ record; build the grove key with
`gdt::interval(v.start, v.end - 1)`.

```cpp
if (auto it = v.info.find("DP"); it != v.info.end()) {
    if (auto* dp = std::get_if<std::vector<int32_t>>(&it->second); dp && !dp->empty()) {
        std::cout << "depth " << (*dp)[0] << "\n";
    }
}
```

::::

::::{tab-item} {{ py_tab }}
:sync: py

`VcfEntry` (read-only):

| Attribute | Type |
|---|---|
| `chrom` | `str` |
| `start`, `end` | `int`, 0-based half-open (`POS - 1`, `start + len(REF)`) |
| `id` | `str`, empty for `.` |
| `ref` | `str` |
| `alt` | `list[str]`; empty for `ALT=.`; symbolic alleles (`<*>`, `<NON_REF>`, `*`) kept verbatim |
| `qual`, `qual_missing` | `float`, and `True` when QUAL is `.` |
| `filter` | `list[str]`; `["PASS"]` when passed, empty for `.` |
| `info` | `dict`; `bool` for Flag, `list[int]` / `list[float]`, `str` |
| `format` | `list[str]` FORMAT keys in column order |
| `samples` | `list[SampleGenotype]`, parallel to `get_sample_names()` |

Methods:

- `passed_filter()` — `True` if FILTER is `PASS` or `.`
- `is_snp()` — single-base REF and a single-base ALT
- `is_indel()` — insertion or deletion
- `VcfEntry.is_symbolic_allele(allele)` — static; `True` for `<*>`, `<NON_REF>`, `*`; such alleles
  are excluded from `is_snp()` / `is_indel()`
- `to_coordinate()` — the grove key as an unstranded `GenomicCoordinate('.', start, end - 1)`
  (0-based closed)
- `to_dict()` — the record's core fields as a JSON-ready `dict`, for use as a `Grove` payload

`info`, `format`, `alt`, `filter` and `samples` are returned as fresh copies on each access.

```python
v.info.get("DP")        # e.g. [37]
```

::::

:::::

## Sample genotypes

Each element of `samples` decodes one sample's FORMAT column.

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

`gio::sample_genotype`: `gt_alleles` (`std::vector<int32_t>`; `0` = REF, `1..` = ALT index,
`-1` = missing), `phased` (`|` separator), `has_gt`, `fields` (`std::unordered_map<std::string,
vcf_format_value>` for everything except GT; `vcf_format_value` is a
`std::variant<std::vector<int32_t>, std::vector<float>, std::string>`). Ragged numeric fields are
trimmed of htslib's vector-end padding.

Methods:

- `gt_string()` — the genotype as written in the file: `"0/1"`, `"0|1"`, `"./."`
- `is_hom_ref()` — every called allele is `0`

::::

::::{tab-item} {{ py_tab }}
:sync: py

`SampleGenotype`: `gt_alleles` (`list[int]`; `0` = REF, `1..` = ALT index, `-1` = missing),
`phased`, `has_gt`, `fields` (`dict` of the other FORMAT keys).

Methods:

- `gt_string()` — the genotype as written in the file: `"0/1"`, `"0|1"`, `"./."`
- `is_hom_ref()` — every called allele is `0`

::::

:::::

## Header access

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

```cpp
const std::string& header            = reader.get_header();
const std::vector<std::string>& names = reader.get_sample_names();   // parallel to entry.samples
const std::vector<std::string>& ctgs  = reader.get_contigs();        // ##contig lines
size_t line = reader.get_current_line();   // 1-based record index, counts skipped records; 0 before the first read
```

::::

::::{tab-item} {{ py_tab }}
:sync: py

```python
reader.get_header()          # raw header text
reader.get_sample_names()    # parallel to entry.samples
reader.get_contigs()         # ##contig names
reader.get_current_line()    # 1-based record index; 0 before the first read
```

::::

:::::

## Loading into a grove

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

```cpp
gst::grove<gdt::interval, std::string> g(100);
for (const auto& v : gio::vcf_reader("calls.vcf.gz", {.skip_filtered = true})) {
    g.insert_data(v.chrom, gdt::interval(v.start, v.end - 1), v.id, gst::sorted);
}
```

::::

::::{tab-item} {{ py_tab }}
:sync: py

There is no typed VCF grove (`VcfEntry` is not serializable); load into the universal `Grove` with
the record's `to_coordinate()` and `to_dict()`:

```python
g = pg.Grove(100)
for v in pg.VcfReader("calls.vcf.gz", skip_filtered=True):
    g.insert(v.chrom, v.to_coordinate(), v.to_dict())
```

::::

:::::