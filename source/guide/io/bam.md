# SAM / BAM Files

SAM, BAM and CRAM files hold sequence alignments: where each sequencing read maps on the genome.
(BAM and CRAM are compressed forms of SAM.) One C++ reader opens all three and detects which it has
been given; CRAM needs its reference genome available to htslib. For CRAM in Python, convert the
file to BAM first (`samtools view -b`). Decompression is done by htslib, the samtools library.
Positions come out **0-based half-open** `[start, end)`: SAM's 1-based POS is converted, and `end` is where the alignment stops on the chromosome, computed from the CIGAR
operations that consume reference bases (those that advance along the chromosome). The CIGAR is
the string that lists how a read lines up with the reference, such as `50M` for 50 matching bases. Convert with
`end - 1` for a {term}`grove` {term}`key` (see {doc}`index`). Filtering by SAM FLAG — unmapped,
**secondary** (an alternative placement of a read), **supplementary** (a further piece of a split
read), **QC-fail** (the sequencer marked the read as low quality), **duplicate** — and by MAPQ (the
mapping quality, a number from 0 to 255 where a higher value means a more certain placement)
happens while reading. The FLAG is the number column of a SAM record that stores these yes/no
properties.

The snippets read `alignments.bam`; substitute any SAM, BAM or CRAM file. If you have none, save the
lines below (tab-separated) as `tiny.sam`, use that name, or make a BAM with `samtools view -b tiny.sam
-o alignments.bam`:

```text
@HD	VN:1.6	SO:coordinate
@SQ	SN:chr1	LN:1000
read1	0	chr1	101	60	10M	*	0	0	ACGTACGTAC	IIIIIIIIII
read2	16	chr1	201	60	10M	*	0	0	ACGTACGTAC	IIIIIIIIII
```

Installation and how to
compile the C++ examples: {doc}`/guide/installation`.

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
                      << " " << aln.get_strand()
                      // mapq is a uint8_t; the cast makes it print as a number, not a character
                      << " MAPQ=" << static_cast<int>(aln.mapq)
                      << " " << aln.cigar_string_repr() << "\n";
        }
    } catch (const std::runtime_error& e) {              // the exception a read failure raises
        std::cerr << "Read error: " << e.what() << "\n";
    }
    return 0;
}
```

The same class reads SAM, BAM and CRAM. Iterating the reader (which calls `read_next()` for each
record) throws on I/O errors **and on truncated auxiliary data** — the optional tags at the end of
a record (`"Truncated auxiliary data at record N"`) — so always wrap BAM iteration in
`try` / `catch`; there is no lenient mode.

::::

::::{tab-item} {{ py_tab }}
:sync: py

```python
import pygenogrove as pg

try:
    for aln in pg.BamReader("alignments.bam"):            # defaults: skip unmapped reads
        print(f"{aln.qname} {aln.chrom}:{aln.start}-{aln.end} {aln.get_strand()} "
              f"MAPQ={aln.mapq} {aln.cigar}")
except RuntimeError as e:
    print("Read error:", e)
```

I/O errors and truncated auxiliary data (the optional tags at the end of a record) raise
`RuntimeError`; there is no lenient mode. SAM and BAM are read by this one class; for CRAM, use the C++ tab or convert to BAM with
`samtools view -b`.

::::

:::::

## Filtering

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

The options (a `struct` is a bundle of named settings; these are the defaults):

```cpp
struct bam_reader_options {
    bool    skip_unmapped      = true;
    bool    skip_secondary     = false;
    bool    skip_supplementary = false;
    bool    skip_qc_fail       = false;
    bool    skip_duplicates    = false;
    uint8_t min_mapq           = 0;      // 0 = no MAPQ filter
};
```

A **preset** is a ready-made options set, called on the type as
`gio::bam_reader_options::name()`. Use one, or set the fields yourself (fragments continuing the
program above, inside `main()`):

```cpp
gio::bam_reader r1("alignments.bam", gio::bam_reader_options::defaults());        // skip unmapped
gio::bam_reader r2("alignments.bam", gio::bam_reader_options::include_all());     // no filtering
gio::bam_reader r3("alignments.bam", gio::bam_reader_options::primary_only());    // primary only
gio::bam_reader r4("alignments.bam", gio::bam_reader_options::high_quality(20));  // MAPQ >= 20

gio::bam_reader_options opts = gio::bam_reader_options::primary_only();   // start from a preset
opts.skip_duplicates = true;                                              // and adjust
opts.min_mapq = 30;
gio::bam_reader r5("alignments.bam", opts);
for (const auto& aln : r5) {                                              // iterate as above
    std::cout << aln.qname << "\n";
}
```

`primary_only()` skips secondary and supplementary alignments; `high_quality(n)` additionally
skips QC-fail and duplicate reads and applies `min_mapq = n`.

::::

::::{tab-item} {{ py_tab }}
:sync: py

The constructor's signature (not runnable code; these are the defaults):

```python
BamReader(path, skip_unmapped=True, skip_secondary=False, skip_supplementary=False,
          skip_qc_fail=False, skip_duplicates=False, min_mapq=0)
```

There are no presets in Python; pass the flags directly:

```python
import pygenogrove as pg

default      = pg.BamReader("alignments.bam")                          # skip unmapped
everything   = pg.BamReader("alignments.bam", skip_unmapped=False)     # no filtering
primary      = pg.BamReader("alignments.bam", skip_secondary=True, skip_supplementary=True)
high_quality = pg.BamReader("alignments.bam", skip_secondary=True, skip_supplementary=True,
                            skip_qc_fail=True, skip_duplicates=True, min_mapq=20)   # MAPQ >= 20
strict       = pg.BamReader("alignments.bam", skip_secondary=True, skip_supplementary=True,
                            skip_duplicates=True, min_mapq=30)
for aln in strict:                                                        # iterate as above
    print(aln.qname)
```

::::

:::::

## The alignment record

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

`gio::sam_entry` (one record type serves SAM, BAM and CRAM):

| Field | Type |
|---|---|
| `qname` | `std::string` read name |
| `chrom` | `std::string` reference name |
| `start`, `end` | `size_t` (unsigned integer), 0-based half-open; `end == start` for unmapped records and for records whose CIGAR consumes no reference bases (e.g. pure soft-clip) |
| `flags` | `alignment_flags` with `is_paired()`, `is_reverse()`, `is_duplicate()`, … — one yes/no test per FLAG bit |
| `mapq` | `uint8_t` (0–255) |
| `cigar` | `std::vector<cigar_element>` — a list of operations, each with `op`, `length`, `to_char()`, `consumes_reference()`, `consumes_query()` |
| `sequence`, `quality` | `std::string` |
| `mate` | `std::optional<mate_info>` (`chrom`, `position`, `insert_size`) — may be absent |
| `tags` | `std::unordered_map<std::string, sam_tag_value>` — tag name → value; the value is a `std::variant` (one of) `char`, `int64_t`, `float`, `std::string` and typed vectors; an `NH:i:1` tag holds the integer 1 |

Helpers: `get_strand()` (`'+'` / `'-'`, `'.'` for an unmapped read), `is_primary()`,
`is_mapped()`, `consumes_reference()`, `cigar_string_repr()`.

Reading one tag, with `aln` from the reading loop above (`NH` is the number of reported alignments
for the read):

```cpp
// find() returns an iterator: a position in the map, or end() when the tag is absent.
// `if (init; cond)` runs the lookup and the test in one statement.
if (auto it = aln.tags.find("NH"); it != aln.tags.end()) {
    // ->second is the value; std::get<int64_t> unpacks the integer alternative of the variant
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
| `start`, `end` | `int`, 0-based half-open; `end == start` for unmapped records and for records whose CIGAR consumes no reference bases (e.g. pure soft-clip) |
| `flags` | `AlignmentFlags` with `value()` and `is_paired()`, `is_reverse()`, `is_duplicate()`, … |
| `mapq` | `int` |
| `cigar` | `str` (string form) |
| `sequence`, `quality` | `str` |

Methods:

- `get_strand()` — `'+'`, `'-'`, or `'.'` for an unmapped read
- `is_primary()` — neither secondary nor supplementary
- `is_mapped()` — the unmapped flag is not set
- `consumes_reference()` — `start < end`; `False` for unmapped reads and for CIGARs that consume
  no reference bases (pure soft-clip, hard-clip-only)
- `to_coordinate()` — the grove key as `GenomicCoordinate(strand, start, end - 1)`
  ({term}`0-based closed`, strand from FLAG); raises `ValueError` for a read that consumes no
  reference bases
- `to_dict()` — the record's core fields as a JSON-ready `dict`, for use as a `Grove`
  {term}`payload`

Both are used in [Loading into a grove](#loading-into-a-grove) below.

The individual FLAG bits live on `aln.flags`, an `AlignmentFlags`:

- `value()` — the raw FLAG integer (column 2 of a SAM line)
- `has_flag(flag)` — test one bit, with the constants on `SamFlags`:
  `aln.flags.has_flag(pg.SamFlags.REVERSE)`
- `is_paired()`, `is_proper_pair()`, `is_unmapped()`, `is_mate_unmapped()`, `is_reverse()`,
  `is_mate_reverse()`, `is_read1()`, `is_read2()`, `is_secondary()`, `is_qc_fail()`,
  `is_duplicate()`, `is_supplementary()` — one test per standard bit, e.g.
  `aln.flags.is_reverse()`

For CIGAR element detail, mate information and auxiliary tags, use the C++ tab; in Python the
`cigar` string carries the operations.

::::

:::::

## Header access

The header is the block of `@` lines at the top of the file: `@HD` (file-level), `@SQ` (one per
reference sequence), `@RG` (read groups) and `@PG` (programs that produced the file).

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

Fragments continuing the first program (`gio` alias, inside `main()`):

```cpp
gio::bam_reader header_reader("alignments.bam");
const std::string& header = header_reader.get_header();                    // full @HD/@SQ/@RG/@PG text
const std::vector<std::string>& refs = header_reader.get_reference_names(); // list of @SQ names
std::cout << header;                                                        // header text
for (const auto& name : refs) std::cout << name << "\n";                    // one @SQ name per line
```

::::

::::{tab-item} {{ py_tab }}
:sync: py

```python
import pygenogrove as pg

reader = pg.BamReader("alignments.bam")
print(reader.get_header(), end="")      # full @HD/@SQ/@RG/@PG text
for name in reader.get_reference_names():   # list of @SQ names
    print(name)                         # one @SQ name per line
```

::::

:::::

## Loading into a grove

A record whose CIGAR consumes no reference bases (unmapped, pure soft-clip `100S`, hard-clip-only
secondary alignments) has `end == start`, so `end - 1` would wrap around to a huge number (the
positions are unsigned). Skip those records with `consumes_reference()` first.

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

```cpp
#include <genogrove/io/bam_reader.hpp>
#include <genogrove/structure/grove/grove.hpp>
#include <genogrove/data_type/interval.hpp>

namespace gio = genogrove::io;
namespace gdt = genogrove::data_type;
namespace gst = genogrove::structure;

int main() {
    gst::grove<gdt::interval, std::string> g(100);   // payload: the read name;
                                                     // 100 = tree order, a good default
    gio::bam_reader reader("alignments.bam");
    for (const auto& aln : reader) {
        if (!aln.consumes_reference()) continue;     // skip records with end == start
        g.insert_data(aln.chrom, gdt::interval(aln.start, aln.end - 1), aln.qname);
    }
    return 0;
}
```

`insert_data` finds the right place itself, so the BAM need not be sorted. The `gst::sorted`
({term}`sorted insert`) tag is the unchecked fast path. Add it only when the records are sorted by
start and then by end, which `samtools sort` does not guarantee: reads with the same start can have
any order of ends. A wrong order silently breaks the tree (see {doc}`/guide/grove/inserting`). `sam_entry` has no `serialize` / `deserialize`, so a grove holding
whole records cannot be saved to disk — this example stores the read name instead.

::::

::::{tab-item} {{ py_tab }}
:sync: py

There is no typed BAM grove (`SamEntry` cannot be saved to disk, so it cannot be a typed-grove
payload); load into the universal `Grove` — the schemaless grove whose payload can be any
JSON-like value — with the record's `to_coordinate()` and the read name as payload, as in C++
(`to_dict()` stores the core fields instead); see
{doc}`/guide/grove/loading_data`:

```python
import pygenogrove as pg

g = pg.Grove(100)                                        # 100 = tree order, a good default
for aln in pg.BamReader("alignments.bam"):
    if aln.consumes_reference():                         # skip records with end == start
        g.insert(aln.chrom, aln.to_coordinate(), aln.qname)
```

`insert` finds the right place itself, so the BAM need not be sorted. `insert_sorted` is the
unchecked fast path; use it only when the keys are sorted by start, then end (and strand), which
`samtools sort` does not guarantee (see {doc}`/guide/grove/inserting`).

::::

:::::
