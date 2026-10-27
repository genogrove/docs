# SAM / BAM Files

SAM, BAM and CRAM files hold sequence alignments. The reader detects the container and decompresses
through htslib. SAM positions are 1-based; the reader converts them to **0-based half-open**
`[start, end)`, computing `end` from the CIGAR string's reference-consuming operations. Filtering
(unmapped, secondary, duplicates, MAPQ) happens while reading.

## Reading alignments

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

```cpp
#include <genogrove/io/bam_reader.hpp>
#include <iostream>

namespace gio = genogrove::io;

int main() {
    gio::bam_reader reader("alignments.bam");            // defaults: skip unmapped reads

    try {
        for (const auto& aln : reader) {
            std::cout << aln.qname << " " << aln.chrom << ":" << aln.start << "-" << aln.end
                      << " " << aln.get_strand() << " MAPQ=" << static_cast<int>(aln.mapq)
                      << " " << aln.cigar_string_repr() << "\n";
        }
    } catch (const std::runtime_error& e) {
        std::cerr << "Read error: " << e.what() << "\n";
    }
    return 0;
}
```

`read_next()` throws on I/O errors **and on truncated auxiliary data**
(`"Truncated auxiliary data at record N"`), so always wrap BAM iteration in `try` / `catch`; there
is no lenient mode.

::::

::::{tab-item} {{ py_tab }}
:sync: py

```python
import pygenogrove as pg

for aln in pg.BamReader("alignments.bam"):            # defaults: skip unmapped reads
    print(aln.qname, aln.chrom, aln.start, aln.end, aln.get_strand(), aln.mapq, aln.cigar)
```

I/O errors and truncated auxiliary data raise `RuntimeError`; there is no lenient mode. CRAM is not
yet exposed in Python.

::::

:::::

## Filtering

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

```cpp
struct bam_reader_options {
    bool    skip_unmapped      = true;
    bool    skip_secondary     = false;
    bool    skip_supplementary = false;
    bool    skip_qc_fail       = false;
    bool    skip_duplicates    = false;
    uint8_t min_mapq           = 0;
};
```

Presets, or set the fields yourself:

```cpp
gio::bam_reader r1("reads.bam", gio::bam_reader_options::defaults());        // skip unmapped
gio::bam_reader r2("reads.bam", gio::bam_reader_options::include_all());     // no filtering
gio::bam_reader r3("reads.bam", gio::bam_reader_options::primary_only());    // primary only
gio::bam_reader r4("reads.bam", gio::bam_reader_options::high_quality(20));  // MAPQ >= 20

gio::bam_reader_options opts = gio::bam_reader_options::primary_only();
opts.skip_duplicates = true;
opts.min_mapq = 30;
gio::bam_reader r5("reads.bam", opts);
```

::::

::::{tab-item} {{ py_tab }}
:sync: py

```python
BamReader(path, skip_unmapped=True, skip_secondary=False, skip_supplementary=False,
          skip_qc_fail=False, skip_duplicates=False, min_mapq=0)
```

```python
pg.BamReader("reads.bam", skip_unmapped=False)                        # everything
pg.BamReader("reads.bam", skip_secondary=True, skip_supplementary=True)   # primary only
pg.BamReader("reads.bam", skip_duplicates=True, min_mapq=30)
```

::::

:::::

## The alignment record

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

`gio::sam_entry`:

| Field | Type |
|---|---|
| `qname` | `std::string` read name |
| `chrom` | `std::string` reference name |
| `start`, `end` | `size_t`, 0-based half-open; `end == start` for unmapped or zero-reference-consuming records |
| `flags` | `alignment_flags` with `is_paired()`, `is_reverse()`, `is_duplicate()`, … |
| `mapq` | `uint8_t` |
| `cigar` | `std::vector<cigar_element>` (`op`, `length`, `to_char()`, `consumes_reference()`, `consumes_query()`) |
| `sequence`, `quality` | `std::string` |
| `mate` | `std::optional<mate_info>` (`chrom`, `position`, `insert_size`) |
| `tags` | `std::unordered_map<std::string, sam_tag_value>`; the value is a `std::variant` of `char`, `int64_t`, `float`, `std::string` and typed vectors |

Helpers: `get_strand()` (`'+'` / `'-'` / `'.'`), `is_primary()`, `is_mapped()`,
`consumes_reference()`, `cigar_string_repr()`.

```cpp
if (auto it = aln.tags.find("NH"); it != aln.tags.end()) {
    std::cout << "hits: " << std::get<int64_t>(it->second) << "\n";
}
```

::::

::::{tab-item} {{ py_tab }}
:sync: py

`SamEntry`:

| Attribute | Type |
|---|---|
| `qname` | `str` read name |
| `chrom` | `str` reference name |
| `start`, `end` | `int`, 0-based half-open; `end == start` for unmapped or zero-reference-consuming records |
| `flags` | `AlignmentFlags` with `value()` and `is_paired()`, `is_reverse()`, `is_duplicate()`, … |
| `mapq` | `int` |
| `cigar` | `str` (string form) |
| `sequence`, `quality` | `str` |

Methods:

- `get_strand()` — `'+'`, `'-'`, or `'.'` for an unmapped read
- `is_primary()` — neither secondary nor supplementary
- `is_mapped()` — the unmapped flag is not set
- `consumes_reference()` — `start < end`; `False` for unmapped reads and for CIGARs that consume no
  reference bases (pure soft-clip, hard-clip-only)
- `to_coordinate()` — the grove key as `GenomicCoordinate(strand, start, end - 1)` (0-based
  closed, strand from FLAG); raises `ValueError` for a read that consumes no reference bases
- `to_dict()` — the record's core fields as a JSON-ready `dict`, for use as a `Grove` payload

The individual FLAG bits live on `aln.flags`, an `AlignmentFlags`:

- `value()` — the raw FLAG integer
- `has_flag(flag)` — test one bit, with the constants on `SamFlags`:
  `aln.flags.has_flag(pg.SamFlags.REVERSE)`
- `is_paired()`, `is_proper_pair()`, `is_unmapped()`, `is_mate_unmapped()`, `is_reverse()`,
  `is_mate_reverse()`, `is_read1()`, `is_read2()`, `is_secondary()`, `is_qc_fail()`,
  `is_duplicate()`, `is_supplementary()` — one test per standard bit, e.g. `aln.flags.is_reverse()`

CIGAR element detail, mate information and auxiliary tags are not yet exposed.

::::

:::::

## Header access

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

```cpp
const std::string& header = reader.get_header();                    // full @HD/@SQ/@RG/@PG text
const std::vector<std::string>& refs = reader.get_reference_names(); // @SQ names
```

::::

::::{tab-item} {{ py_tab }}
:sync: py

```python
reader.get_header()              # full @HD/@SQ/@RG/@PG text
reader.get_reference_names()     # list of @SQ names
```

::::

:::::

## Loading into a grove

A record whose CIGAR consumes no reference bases (unmapped, pure soft-clip `100S`, hard-clip-only
secondary alignments) has `end == start`; converting it to a closed interval would underflow. Gate
on `consumes_reference()` first.

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

```cpp
gst::grove<gdt::interval, std::string> g(100);
for (const auto& aln : reader) {
    if (!aln.consumes_reference()) continue;
    g.insert_data(aln.chrom, gdt::interval(aln.start, aln.end - 1), aln.qname, gst::sorted);
}
```

::::

::::{tab-item} {{ py_tab }}
:sync: py

There is no typed BAM grove (`SamEntry` is not serializable); load into the universal `Grove` with
the record's `to_coordinate()` and `to_dict()`:

```python
g = pg.Grove(100)
for aln in pg.BamReader("reads.bam"):
    if aln.consumes_reference():
        g.insert(aln.chrom, aln.to_coordinate(), aln.to_dict())
```

::::

:::::