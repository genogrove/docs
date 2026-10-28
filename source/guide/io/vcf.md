# VCF / BCF Files

VCF and BCF files hold variant calls. One reader handles plain VCF, block-compressed (`bgzip`) VCF
and binary BCF, and tells them apart itself. Coordinates are **0-based half-open**:
`start = POS - 1` and `end = start + len(REF)`, so a SNP spans one base. Convert with `end - 1`
for a {term}`grove` {term}`key` — the same rule as BED and BAM, not the GFF one (see
{doc}`index`).

The snippets read `calls.vcf.gz`; substitute any VCF or BCF file. Installation and how to compile
the C++ examples: {doc}`/guide/installation`.

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
            // one genotype per sample, e.g. "0/1" — see "Sample genotypes" below
            for (const auto& s : v.samples) std::cout << " " << s.gt_string();
            std::cout << "\n";
        }
    } catch (const std::runtime_error& e) {              // the exception a read failure raises
        std::cerr << "Read error: " << e.what() << "\n";
    }
    return 0;
}
```

The constructor's signature and options (a declaration, not runnable code):

```cpp
vcf_reader(const std::string& path, vcf_reader_options options = {});   // = {}: defaults
struct vcf_reader_options {
    bool parse_info    = true;    // parse the INFO column into `info` (false: leave it empty)
    bool parse_samples = true;    // decode the per-sample FORMAT columns into `samples`
    bool skip_filtered = false;   // drop records that did not pass FILTER
    std::string region = "";      // tabix/CSI region, see below
};
```

Presets (ready-made option sets, called on the type): `vcf_reader_options::defaults()` is the
values above; `vcf_reader_options::sites_only()` sets `parse_samples = false`. `region` restricts
reading to one locus of an indexed file — see {doc}`region_access`.

::::

::::{tab-item} {{ py_tab }}
:sync: py

```python
import pygenogrove as pg

for v in pg.VcfReader("calls.vcf.gz"):
    if v.is_snp():
        kind = "SNP"
    elif v.is_indel():
        kind = "indel"
    else:
        kind = ""
    genotypes = [s.gt_string() for s in v.samples]   # one per sample, e.g. "0/1" — see below
    print(v.chrom, v.start, v.end, v.ref, v.alt, kind, genotypes)
```

The constructor's signature (not runnable code):

```python
VcfReader(path, parse_info=True, parse_samples=True, skip_filtered=False, region="")
```

`parse_info=False` leaves `info` empty; `parse_samples=False` skips the per-sample FORMAT columns
(the equivalent of the C++ `sites_only()` preset — there are no presets in Python);
`skip_filtered=True` drops records that did not pass FILTER; `region` restricts reading to one
locus of an indexed file — see {doc}`region_access`.

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
| `start`, `end` | `size_t` (unsigned integer), 0-based half-open (`POS - 1`, `start + len(REF)`) |
| `id` | `std::string`, empty for `.` |
| `ref` | `std::string` |
| `alt` | `std::vector<std::string>` (a list); empty for `ALT=.`; symbolic alleles (`<*>`, `<NON_REF>`, `*`) kept verbatim |
| `qual`, `qual_missing` | `float`, and `true` when QUAL is `.` |
| `filter` | `std::vector<std::string>`; `{"PASS"}` when passed, empty for `.` |
| `info` | `vcf_info` = `std::unordered_map<std::string, vcf_info_value>` (INFO key → value); the value is a `std::variant<bool, std::vector<int32_t>, std::vector<float>, std::string>`, i.e. one of Flag, Integer, Float, String — numeric fields are always lists, even for a single value |
| `format` | `std::vector<std::string>` FORMAT keys in column order |
| `samples` | `std::vector<sample_genotype>`, parallel to `get_sample_names()` |

Methods:

- `passed_filter()` — `true` if FILTER is `PASS` or `.`
- `is_snp()` — single-base REF and exactly **one** single-base, non-symbolic ALT (a multi-allelic
  record such as `A → C,G` is not a SNP)
- `is_indel()` — at least one non-symbolic ALT whose length differs from REF
- `static is_symbolic_allele(allele)` — called on the type,
  `gio::vcf_entry::is_symbolic_allele(a)`, not on a record; `true` for anything that is not a plain
  base sequence: `<…>` alleles (`<*>`, `<NON_REF>`, `<DEL>`, …), `*`, `.`, breakend notation
  containing `[` or `]`, and the empty string; such alleles are excluded from `is_snp()` /
  `is_indel()`

There is no coordinate helper on the C++ record; build the grove key with
`gdt::interval(v.start, v.end - 1)`.

Reading one INFO field, with `v` from the reading loop above:

```cpp
// find() returns an iterator: a position in the map, or end() when the key is absent.
// `if (init; cond)` runs the lookup and the test in one statement.
if (auto it = v.info.find("DP"); it != v.info.end()) {
    // std::get_if asks the variant for its integer-list alternative: a pointer to it,
    // or null if DP holds another type. `&it->second` is the address of the value.
    if (auto* dp = std::get_if<std::vector<int32_t>>(&it->second); dp && !dp->empty()) {
        std::cout << "depth " << (*dp)[0] << "\n";   // *dp: the list itself; [0]: its first value
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
| `info` | `dict`; `bool` for Flag, `list[int]` / `list[float]` (always lists, even for a single value), `str` |
| `format` | `list[str]` FORMAT keys in column order |
| `samples` | `list[SampleGenotype]`, parallel to `get_sample_names()` |

Methods:

- `passed_filter()` — `True` if FILTER is `PASS` or `.`
- `is_snp()` — single-base REF and exactly **one** single-base, non-symbolic ALT (a multi-allelic
  record such as `A → C,G` is not a SNP)
- `is_indel()` — at least one non-symbolic ALT whose length differs from REF
- `VcfEntry.is_symbolic_allele(allele)` — static, i.e. called on the class rather than on a
  record; `True` for anything that is not a plain base sequence: `<…>` alleles (`<*>`,
  `<NON_REF>`, `<DEL>`, …), `*`, `.`, breakend notation containing `[` or `]`, and the empty
  string; such alleles are excluded from `is_snp()` / `is_indel()`
- `to_coordinate()` — the grove key as an unstranded `GenomicCoordinate('.', start, end - 1)`
  ({term}`0-based closed`); raises `ValueError` for a record that spans no reference bases
  (`end <= start`)
- `to_dict()` — the record's core fields as a JSON-ready `dict`, for use as a `Grove`
  {term}`payload`

`info`, `format`, `alt`, `filter` and `samples` are returned as fresh copies on each access, so
modifying what you get back (e.g. `v.info["DP"] = [0]`) does nothing to the record.

Reading one INFO field, with `v` from the reading loop above:

```python
print(v.info.get("DP"))     # e.g. [37]; None when absent
```

::::

:::::

## Sample genotypes

Each element of `samples` decodes one sample's FORMAT column.

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

`gio::sample_genotype`: `gt_alleles` (`std::vector<int32_t>`, a list; `0` = REF, `1..` = ALT
index, `-1` = missing), `phased` (`|` separator), `has_gt`, `fields`
(`std::unordered_map<std::string, vcf_format_value>`: FORMAT key → value for everything except GT;
`vcf_format_value` is a `std::variant<std::vector<int32_t>, std::vector<float>, std::string>`,
i.e. one of an integer list, a float list or a string). Ragged numeric fields (a different number
of values per sample) are trimmed of the padding htslib adds to make them equal length.

Methods:

- `gt_string()` — the genotype rebuilt from `gt_alleles` and `phased`: `"0/1"`, `"0|1"`, `"./."`.
  One phasing flag covers the whole genotype, so a mixed-phase genotype like `0|1/2` comes back
  with a single separator; empty string when the sample has no GT
- `is_hom_ref()` — `true` only when GT is present and **every** allele is `0`; a missing allele
  (`./0`, `./.`) makes it `false`

::::

::::{tab-item} {{ py_tab }}
:sync: py

`SampleGenotype`: `gt_alleles` (`list[int]`; `0` = REF, `1..` = ALT index, `-1` = missing),
`phased`, `has_gt`, `fields` (`dict` of the other FORMAT keys; each value is a `list[int]`,
`list[float]` or `str`). Ragged numeric fields (a different number of values per sample) are
trimmed of the padding htslib adds to make them equal length.

Methods:

- `gt_string()` — the genotype rebuilt from `gt_alleles` and `phased`: `"0/1"`, `"0|1"`, `"./."`.
  One phasing flag covers the whole genotype, so a mixed-phase genotype like `0|1/2` comes back
  with a single separator; empty string when the sample has no GT
- `is_hom_ref()` — `True` only when GT is present and **every** allele is `0`; a missing allele
  (`./0`, `./.`) makes it `False`

::::

:::::

## Header access

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

Fragments continuing the first program (`gio` alias, inside `main()`):

```cpp
gio::vcf_reader reader("calls.vcf.gz");
const std::string& header            = reader.get_header();
const std::vector<std::string>& names = reader.get_sample_names();   // parallel to v.samples
const std::vector<std::string>& ctgs  = reader.get_contigs();        // ##contig lines
size_t line = reader.get_current_line();   // 1-based record index (counts skipped records);
                                           // 0 before the first read
```

::::

::::{tab-item} {{ py_tab }}
:sync: py

```python
import pygenogrove as pg

reader = pg.VcfReader("calls.vcf.gz")
print(reader.get_header())          # raw header text
print(reader.get_sample_names())    # parallel to v.samples
print(reader.get_contigs())         # ##contig names
print(reader.get_current_line())    # 1-based record index (counts skipped records);
                                    # 0 before the first read
```

::::

:::::

## Loading into a grove

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

```cpp
#include <genogrove/io/vcf_reader.hpp>
#include <genogrove/structure/grove/grove.hpp>
#include <genogrove/data_type/interval.hpp>

namespace gio = genogrove::io;
namespace gdt = genogrove::data_type;
namespace gst = genogrove::structure;

int main() {
    gst::grove<gdt::interval, std::string> g(100);   // payload: the ID column;
                                                     // 100 = tree order, a good default
    // {.skip_filtered = true} sets one option and leaves the rest at their defaults
    for (const auto& v : gio::vcf_reader("calls.vcf.gz", {.skip_filtered = true})) {
        g.insert_data(v.chrom, gdt::interval(v.start, v.end - 1), v.id, gst::sorted);
    }
    return 0;
}
```

The payload here is `v.id`, which is the empty string for records whose ID column is `.`; pick
another field (or build a string from several) if your file has no IDs. `gst::sorted`
({term}`sorted insert`) is a promise that the file is position-sorted, as VCFs normally are; that
path does not check, so drop the tag if yours is not (see {doc}`/guide/grove/inserting`).

::::

::::{tab-item} {{ py_tab }}
:sync: py

There is no typed VCF grove (`VcfEntry` cannot be saved to disk, so it cannot be a typed-grove
payload); load into the universal `Grove` — the schemaless grove whose payload can be any
JSON-like value — with the record's `to_coordinate()` (an unstranded coordinate, strand `'.'`) and
`to_dict()` (see {doc}`/guide/grove/loading_data`):

```python
import pygenogrove as pg

g = pg.Grove(100)                                        # 100 = tree order, a good default
for v in pg.VcfReader("calls.vcf.gz", skip_filtered=True):
    g.insert(v.chrom, v.to_coordinate(), v.to_dict())
```

`insert` finds the right place itself, so the file need not be sorted; `insert_sorted` is the
unchecked fast path for a position-sorted file (see {doc}`/guide/grove/inserting`).

::::

:::::
