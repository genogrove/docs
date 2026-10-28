# GFF3 / GTF Files

GFF3 and GTF files hold gene annotations, one feature (gene, transcript, exon, …) per line. One
reader handles both: it detects the format from the attribute column — the ninth column, written
`key=value` in GFF3 and `key "value"` in GTF. Plain and gzip/bgzip-compressed (`.gz`) files are
detected automatically. Coordinates are **1-based closed** `[start, end]`; convert with
`start - 1`, `end - 1` for a {term}`grove` {term}`key` (see {doc}`index`).

The snippets read `annotations.gtf.gz`; substitute any GFF3 or GTF file. If you have none, save these
two tab-separated lines as `annotations.gtf` and use that name:

```text
chr1	src	gene	101	200	.	+	.	gene_id "g1"; gene_name "geneA";
chr1	src	exon	101	150	.	+	.	gene_id "g1"; transcript_id "t1";
```

Installation and how to
compile the C++ examples: {doc}`/guide/installation`.

## Reading a GFF/GTF file

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

```cpp
#include <genogrove/io/gff_reader.hpp>
#include <iostream>

namespace gio = genogrove::io;

int main() {
    gio::gff_reader reader("annotations.gtf.gz");

    try {
        for (const auto& entry : reader) {
            std::cout << entry.seqid << " " << entry.type << " "
                      << entry.start << "-" << entry.end;
            // get_gene_id() returns an optional: `if (id)` tests whether a gene_id
            // was present, `*id` reads it
            if (auto id = entry.get_gene_id()) std::cout << " " << *id;
            // `cond ? a : b` picks a when cond is true, b otherwise
            std::cout << (entry.is_gtf() ? " [GTF]" : " [GFF3]") << "\n";
        }
    } catch (const std::runtime_error& e) {              // the exception a bad line raises
        std::cerr << "Parse error: " << e.what() << "\n";
    }
    return 0;
}
```

The constructor's signature and options (a declaration, not runnable code):

```cpp
explicit gff_reader(const std::filesystem::path& path);                              // default options
gff_reader(const std::filesystem::path& path, const gff_reader_options& options);
struct gff_reader_options {
    bool skip_invalid_lines = false;   // skip malformed lines instead of throwing
    bool validate_gtf = false;         // enforce mandatory GTF attributes, see "GTF validation"
    std::string region = "";           // tabix region, see below
};
```

`region` restricts reading to one locus of an indexed `.gz` file — see {doc}`region_access`.

::::

::::{tab-item} {{ py_tab }}
:sync: py

```python
import pygenogrove as pg

for entry in pg.GffReader("annotations.gtf.gz"):
    tag = "GTF" if entry.is_gtf() else "GFF3"
    print(entry.seqid, entry.type, entry.start, entry.end, entry.get_gene_id(), tag)
```

The constructor's signature (not runnable code):

```python
GffReader(path: str, skip_invalid_lines: bool = False, validate_gtf: bool = False,
          region: str = "")
```

`skip_invalid_lines=True` skips malformed lines instead of raising; `validate_gtf=True` enforces
the mandatory GTF attributes (see [GTF validation](#gtf-validation)); `region` restricts reading to
one locus of an indexed `.gz` file — see {doc}`region_access`.

::::

:::::

## The GFF record

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

`gio::gff_entry`:

| Field | Type | Column |
|---|---|---|
| `seqid` | `std::string` | 1 |
| `source` | `std::string` | 2 |
| `type` | `std::string` (`gene`, `exon`, `CDS`, …) | 3 |
| `start`, `end` | `size_t` (unsigned integer; 1-based closed) | 4, 5 |
| `score` | `std::optional<double>` (`nullopt` for `.`) | 6 |
| `strand` | `std::optional<char>` (`'+'`, `'-'`, `'.'`, `'?'`) | 7 |
| `phase` | `std::optional<int>` (0, 1 or 2: how many bases to skip to reach the next codon; CDS only) | 8 |
| `attributes` | `std::map<std::string, std::string, std::less<>>` — a sorted key → value map; the `std::less<>` part only lets `find` accept any string type | 9 |
| `format` | `gff_format::GFF3` / `GTF` / `UNKNOWN` (named constants) | — |

`std::optional<T>` is "a `T` that may be absent": test it like a bool, then read it with `*`.

A record can also be built by hand — `gff_entry()` or `gff_entry(seqid, start, end, type)` — and
all fields are plain members you can read and assign.

Methods:

- `is_gtf()`, `is_gff3()` — the detected format
- `get_attribute(key)` and the named attribute helpers — see [Attributes](#attributes)
- `serialize(os)`, `static deserialize(is)` — binary {term}`serialization`, so a
  `grove<gdt::interval, gio::gff_entry>` (a grove whose {term}`payload` is the whole record) can be
  saved to disk directly; this is what the {term}`CLI`'s `idx` command writes for GFF input (see
  {doc}`/cli`)

There is no coordinate helper on the C++ record; build the grove key with
`gdt::interval(e.start - 1, e.end - 1)`.

::::

::::{tab-item} {{ py_tab }}
:sync: py

`GffEntry` — attributes are read/write:

| Attribute | Type | Column |
|---|---|---|
| `seqid` | `str` | 1 |
| `source` | `str` | 2 |
| `type` | `str` (`gene`, `exon`, `CDS`, …) | 3 |
| `start`, `end` | `int` (1-based closed) | 4, 5 |
| `score` | `Optional[float]` | 6 |
| `strand` | `Optional[str]`, one of `'+'`, `'-'`, `'.'`, `'?'` | 7 |
| `phase` | `Optional[int]` (0, 1, 2; CDS only) | 8 |
| `attributes` | `dict[str, str]` (returned and assigned by copy, so `entry.attributes["x"] = "y"` does not stick — assign a whole dict) | 9 |
| `format` | `GffFormat.GFF3` / `GTF` / `UNKNOWN` | — |

`Optional[float]` means "a `float`, or `None` when the column is `.`" (the same for the other `Optional` types): test it with `is not None`.

Constructors: `GffEntry()` and `GffEntry(seqid, start, end, type)`. `repr(entry)` shows the record.

Methods:

- `is_gtf()`, `is_gff3()` — the detected format
- `get_attribute(key)` and the named attribute helpers — see [Attributes](#attributes)

There is no `to_coordinate()` on `GffEntry`: `GffGrove.insert(index, entry)` derives the grove key
from the record, which becomes the payload (see {doc}`/guide/grove/loading_data`).

::::

:::::

## Attributes

Column 9 is parsed into a key → value map. Helpers look up the common keys and paper over the
GFF3/GTF naming differences. Semicolons inside quoted GTF values (`gene_name "a;b"`) are kept as
part of the value; GFF3 writes a literal semicolon inside a value as `%3B` (a percent-encoded character), as the spec requires.

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

| Helper | Returns | Looks up |
|---|---|---|
| `get_gene_id()` | `std::optional<std::string>` | `gene_id` |
| `get_transcript_id()` | `std::optional<std::string>` | `transcript_id` |
| `get_exon_number()` | `std::optional<int>` | `exon_number` |
| `get_gene_name()` | `std::optional<std::string>` | `gene_name`, then GFF3 `Name` |
| `get_gene_biotype()` | `std::optional<std::string>` | `gene_biotype`, `gene_type`, `biotype` |
| `get_attribute(key)` | `std::optional<std::string>` | any key (`key` may be any string type) |

Direct map access, with `entry` from the reading loop above:

```cpp
// find() returns an iterator: a position in the map, or end() when the key is absent.
// `if (init; cond)` runs the lookup and the test in one statement.
if (auto it = entry.attributes.find("ID"); it != entry.attributes.end()) {
    std::cout << it->second << "\n";          // ->first is the key, ->second the value
}
```

::::

::::{tab-item} {{ py_tab }}
:sync: py

| Helper | Returns | Looks up |
|---|---|---|
| `get_gene_id()` | `Optional[str]` | `gene_id` |
| `get_transcript_id()` | `Optional[str]` | `transcript_id` |
| `get_exon_number()` | `Optional[int]` | `exon_number` |
| `get_gene_name()` | `Optional[str]` | `gene_name`, then GFF3 `Name` |
| `get_gene_biotype()` | `Optional[str]` | `gene_biotype`, `gene_type`, `biotype` |
| `get_attribute(key)` | `Optional[str]` | any key |

Direct dict access, with `entry` from the reading loop above:

```python
print(entry.attributes.get("ID"))     # entry.attributes is a copy of the dict
```

::::

:::::

## GTF validation

Mandatory GTF attributes (the required attributes of the GTF 2 format) are checked only on request: with `validate_gtf` enabled,
`gene_id` is required on every feature (every line) and `transcript_id` on `exon`, `CDS`,
`start_codon`, `stop_codon`, `UTR`, `5UTR` and `3UTR` (the 5' and 3' untranslated regions). A failing record throws, or is skipped under
`skip_invalid_lines`. GFF3 files are unaffected.

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

Fragments continuing the first program (`gio` alias, inside `main()`); `{.field = value}` sets
named options and leaves the rest at their defaults:

```cpp
gio::gff_reader strict("annotations.gtf.gz", gio::gff_reader_options{.validate_gtf = true});
gio::gff_reader lenient("annotations.gtf.gz",
    gio::gff_reader_options{.skip_invalid_lines = true, .validate_gtf = true});

for (const auto& entry : lenient) {           // only records passing validation arrive here
    std::cout << entry.type << "\n";
}
```

::::

::::{tab-item} {{ py_tab }}
:sync: py

```python
import pygenogrove as pg

strict  = pg.GffReader("annotations.gtf.gz", validate_gtf=True)
lenient = pg.GffReader("annotations.gtf.gz", skip_invalid_lines=True, validate_gtf=True)

for entry in lenient:                         # only records passing validation arrive here
    print(entry.type)
```

::::

:::::

## Loading into a grove

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

```cpp
#include <genogrove/io/gff_reader.hpp>
#include <genogrove/structure/grove/grove.hpp>
#include <genogrove/data_type/interval.hpp>

namespace gio = genogrove::io;
namespace gdt = genogrove::data_type;
namespace gst = genogrove::structure;

int main() {
    gst::grove<gdt::interval, std::string> g(100);   // payload: the gene ID;
                                                     // 100 = tree order, a good default
    gio::gff_reader reader("annotations.gtf.gz");
    for (const auto& e : reader) {
        auto gene_id = e.get_gene_id();
        if (e.type != "gene" || !gene_id) continue;  // skip anything but genes with an ID
        g.insert_data(e.seqid, gdt::interval(e.start - 1, e.end - 1), *gene_id);   // *: the ID
    }
    return 0;
}
```

GFF files are often but not always position-sorted. Add `gst::sorted` ({term}`sorted insert`) as
the last argument only when you know the file is sorted by start and then by end. Sorting by start
alone is not enough, because two records with the same start must come in order of their end. That
path does not check, and a wrong order silently breaks the tree (see
{doc}`/guide/grove/inserting`).

::::

::::{tab-item} {{ py_tab }}
:sync: py

`GffGrove.insert(index, entry)` derives the {term}`0-based closed` key from the 1-based record:

```python
import pygenogrove as pg

g = pg.GffGrove(100)                                     # 100 = tree order, a good default
for e in pg.GffReader("annotations.gtf.gz"):
    if e.type == "gene":
        g.insert(e.seqid, e)
```

Every gene is inserted, with or without a `gene_id`: here the payload is the whole `GffEntry`, so a
missing ID costs nothing, whereas in the C++ example the ID *is* the payload and records without one
are skipped.

Sortedness: `insert` finds the right place itself, so the file need not be sorted.
`insert_bulk(index, entries)` sorts the list you give it, but it only appends to the index. If the
index already holds keys, every new key must be greater than all existing keys, whatever the value of
`presorted`. The code does not check this, so use `insert_bulk` on an empty index. Pass
`presorted=True` only when the list is already ordered by start and then end. See
{doc}`/guide/grove/loading_data` for the typed groves.

::::

:::::
