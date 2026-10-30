# VCF / BCF Files

VCF and BCF files hold variant calls: positions where a sample differs from the reference genome.
Each record has fixed columns: `POS` (1-based position), `REF` (the reference bases), `ALT` (the
alternative bases), `QUAL` (confidence), `FILTER` (`PASS` or the reason a call failed) and `INFO`
(extra facts about the site). Optional per-sample columns (`FORMAT` and one column per sample) hold
each sample's genotype, such as `0/1`. A SNP is a change of one base. One reader handles plain VCF, block-compressed (`bgzip`) VCF
and binary BCF, and tells them apart itself. Coordinates are **0-based half-open**:
`start = POS - 1` and `end = start + len(REF)`, so a SNP spans one base. `to_interval()` and
`to_coordinate()` subtract 1 from `end` to give a {term}`grove` {term}`key` — the same rule as BED
and BAM, not the GFF one (see {doc}`index`).

The snippets read `calls.vcf.gz`; substitute any VCF or BCF file. If you have none, save these lines
(the columns are tab-separated) as `calls.vcf` and use that name:

```text
##fileformat=VCFv4.2
##contig=<ID=chr1>
#CHROM	POS	ID	REF	ALT	QUAL	FILTER	INFO	FORMAT	sample1
chr1	100	rs1	A	G	50	PASS	DP=12	GT	0/1
chr1	200	.	AT	A	40	PASS	DP=8	GT	1/1
```

Installation and how to compile
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
explicit vcf_reader(const std::filesystem::path& path);                              // default options
vcf_reader(const std::filesystem::path& path, const vcf_reader_options& options);
struct vcf_reader_options {
    bool parse_info    = true;    // parse the INFO column into `info` (false: leave it empty)
    bool parse_samples = true;    // decode the per-sample FORMAT columns into `samples`
    bool skip_filtered = false;   // drop records whose FILTER is neither PASS nor "."
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

try:
    for v in pg.VcfReader("calls.vcf.gz"):
        line = f"{v.chrom}:{v.start}-{v.end} REF={v.ref}"
        if not v.qual_missing: line += f" QUAL={v.qual:g}"       # 50, not 50.0
        if v.is_snp():      line += " SNP"
        elif v.is_indel():  line += " indel"
        # one genotype per sample, e.g. "0/1" — see "Sample genotypes" below
        for s in v.samples: line += " " + s.gt_string()
        print(line)
except RuntimeError as e:
    print("Read error:", e)
```

The constructor's signature (not runnable code):

```python
VcfReader(path, parse_info=True, parse_samples=True, skip_filtered=False, region="")
```

`parse_info=False` leaves `info` empty; `parse_samples=False` skips the per-sample FORMAT columns
(the equivalent of the C++ `sites_only()` preset — there are no presets in Python);
`skip_filtered=True` drops records whose FILTER is neither `PASS` nor `.`; `region` restricts reading to one
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
| `info` | `vcf_info` = `std::unordered_map<std::string, vcf_info_value>` (INFO key → value); the value is a `std::variant<bool, std::vector<int32_t>, std::vector<float>, std::string>`, i.e. one of Flag, Integer, Float, String — numeric fields are always lists, even for a single value (`DP=12` holds the list `{12}`) |
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
- `gdt::interval to_interval() const` — the grove key `[start, end - 1]`. It does not check the
  record. A parsed record always has `end > start`. A record that your own code creates, not a
  reader, can break this rule: with `0 < end <= start` the key constructor throws
  `std::invalid_argument`, and with `end == 0` the key is a huge number that the constructor accepts
- `gdt::genomic_coordinate to_coordinate() const` — the same key, unstranded (strand `.`, which
  means none)

Reading one INFO field, with `v` from the reading loop above:

```cpp
auto it = v.info.find("DP");                     // the map position of "DP", or end() if absent
if (it != v.info.end()) {
    // std::get_if returns a pointer to the integer list if DP holds one, otherwise a null pointer
    auto* depth = std::get_if<std::vector<int32_t>>(&it->second);
    if (depth != nullptr && !depth->empty()) {
        std::cout << "depth " << (*depth)[0] << "\n";   // the first value of the list
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
- `to_coordinate()` — the grove key as an unstranded `GenomicCoordinate('.', start, end - 1)` (strand `.` means none)
  ({term}`0-based closed`); raises `ValueError` for a record that spans no reference bases
  (`end <= start`)
- `to_dict()` — the record's core fields as a JSON-ready `dict`, for use as a `Grove`
  {term}`payload`

`info`, `format`, `alt`, `filter` and `samples` are returned as fresh copies on each access, so
modifying what you get back (e.g. `v.info["DP"] = [0]`) does nothing to the record.

Reading one INFO field, with `v` from the reading loop above:

```python
dp = v.info.get("DP")           # the list [12] for DP=12; None when absent
if dp:
    print("depth", dp[0])       # the first value of the list
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
i.e. one of an integer list, a float list or a string). Numeric fields can have a different
number of values per sample; htslib pads them to equal length, and the reader removes that padding.

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
gio::vcf_reader header_reader("calls.vcf.gz");
const std::string& header            = header_reader.get_header();
const std::vector<std::string>& names = header_reader.get_sample_names();   // parallel to v.samples
const std::vector<std::string>& ctgs  = header_reader.get_contigs();        // ##contig lines
size_t line = header_reader.get_current_line();   // 1-based record index (counts skipped records);
                                           // 0 before the first read
std::cout << header;                                         // raw header text
for (const auto& n : names) std::cout << n << "\n";          // one sample name per line
for (const auto& c : ctgs)  std::cout << c << "\n";          // one contig name per line
std::cout << line << "\n";                                   // 0: nothing read yet
```

::::

::::{tab-item} {{ py_tab }}
:sync: py

```python
import pygenogrove as pg

reader = pg.VcfReader("calls.vcf.gz")
print(reader.get_header(), end="")  # raw header text
for n in reader.get_sample_names():  # parallel to v.samples
    print(n)                        # one sample name per line
for c in reader.get_contigs():       # ##contig names
    print(c)                        # one contig name per line
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
        g.insert_data(v.chrom, v.to_interval(), v.id);
    }
    return 0;
}
```

The payload here is `v.id`, which is the empty string for records whose ID column is `.`; pick
another field (or build a string from several) if your file has no IDs. `insert_data` finds the
right place itself, so the VCF need not be sorted. The `gst::sorted` ({term}`sorted insert`) tag is
the unchecked fast path. Add it only when the records are sorted by start and then by end. A
position-sorted VCF is sorted by start only: two records at the same position (for example an SNP and
a deletion) can come with their ends in any order. A wrong order silently breaks the tree (see
{doc}`/guide/grove/inserting`).

::::

::::{tab-item} {{ py_tab }}
:sync: py

There is no typed VCF grove (`VcfEntry` cannot be saved to disk, so it cannot be a typed-grove
payload); load into the universal `Grove` — the schemaless grove whose payload can be any
JSON-like value — with the record's `to_coordinate()` (an unstranded coordinate, strand `'.'`) and
the ID column as payload, as in C++ (see {doc}`/guide/grove/loading_data`):

```python
import pygenogrove as pg

g = pg.Grove(100)                                        # 100 = tree order, a good default
for v in pg.VcfReader("calls.vcf.gz", skip_filtered=True):
    g.insert(v.chrom, v.to_coordinate(), v.id)
```

`to_dict()` stores the core fields of the record as payload instead.

`insert` finds the right place itself, so the file need not be sorted. `insert_sorted` is the
unchecked fast path; use it only when the keys are sorted by start, then end (and strand), which a
position-sorted VCF does not guarantee (see {doc}`/guide/grove/inserting`).

::::

:::::
