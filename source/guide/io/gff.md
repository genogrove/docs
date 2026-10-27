# GFF3 / GTF Files

GFF3 and GTF files hold gene annotations. One reader handles both: it detects the dialect from the
attribute column (`key=value` for GFF3, `key "value"` for GTF). Coordinates are **1-based closed**
`[start, end]`; convert with `start - 1`, `end - 1` for a grove key (see {doc}`index`).

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
            if (auto id = entry.get_gene_id()) std::cout << " " << *id;
            std::cout << (entry.is_gtf() ? " [GTF]" : " [GFF3]") << "\n";
        }
    } catch (const std::runtime_error& e) {
        std::cerr << "Parse error: " << e.what() << "\n";
    }
    return 0;
}
```

```cpp
gff_reader(const std::string& path, gff_reader_options options = {});
struct gff_reader_options {
    bool skip_invalid_lines = false;   // skip malformed lines instead of throwing
    bool validate_gtf = false;         // enforce mandatory GTF2 attributes
    std::string region = "";           // tabix region, see region_access
};
```

::::

::::{tab-item} {{ py_tab }}
:sync: py

```python
import pygenogrove as pg

for entry in pg.GffReader("annotations.gtf.gz"):
    tag = "GTF" if entry.is_gtf() else "GFF3"
    print(entry.seqid, entry.type, entry.start, entry.end, entry.get_gene_id(), tag)
```

```python
GffReader(path: str, skip_invalid_lines: bool = False, validate_gtf: bool = False,
          region: str = "")
```

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
| `start`, `end` | `size_t` (1-based closed) | 4, 5 |
| `score` | `std::optional<double>` (`nullopt` for `.`) | 6 |
| `strand` | `std::optional<char>` (`'+'`, `'-'`, `'.'`, `'?'`) | 7 |
| `phase` | `std::optional<int>` (0, 1, 2; CDS only) | 8 |
| `attributes` | `std::map<std::string, std::string, std::less<>>` | 9 |
| `format` | `gff_format::GFF3` / `GTF` / `UNKNOWN` | — |

`gff_entry` has `serialize` / `deserialize` members, so a `grove<gdt::interval, gio::gff_entry>` can
be persisted directly — this is what the CLI's `idx` writes for GFF input.

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
| `attributes` | `dict[str, str]` (returned and assigned by copy) | 9 |
| `format` | `GffFormat.GFF3` / `GTF` / `UNKNOWN` | — |

Records can be built by hand (`GffEntry(seqid, start, end, type)`). `GffEntry` is the payload type
of `GffGrove` (see {doc}`/guide/grove/loading_data`).

::::

:::::

## Attributes

Column 9 is parsed into a key → value map. Helpers look up the common keys and paper over the
GFF3/GTF naming differences. Semicolons inside quoted GTF values (`gene_name "a;b"`) are kept as
part of the value; GFF3 uses `%3B` for a literal semicolon as the spec requires.

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
| `get_attribute(key)` | `std::optional<std::string>` | any key (`std::string_view`) |

```cpp
if (auto it = entry.attributes.find("ID"); it != entry.attributes.end()) {   // direct map access
    std::cout << it->second << "\n";
}
```

`is_gtf()` / `is_gff3()` report the detected dialect.

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

```python
entry.attributes.get("ID")        # direct dict access (a copy of the map)
```

`is_gtf()` / `is_gff3()` report the detected dialect.

::::

:::::

## GTF validation

Mandatory GTF2 attributes are checked only on request: with `validate_gtf` enabled, `gene_id` is
required on every feature and `transcript_id` on `exon`, `CDS`, `start_codon`, `stop_codon`, `UTR`,
`5UTR` and `3UTR`. A failing record throws, or is skipped under `skip_invalid_lines`. GFF3 files are
unaffected.

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

```cpp
gio::gff_reader strict("annotations.gtf", gio::gff_reader_options{.validate_gtf = true});
gio::gff_reader lenient("annotations.gtf",
    gio::gff_reader_options{.skip_invalid_lines = true, .validate_gtf = true});
```

::::

::::{tab-item} {{ py_tab }}
:sync: py

```python
strict  = pg.GffReader("annotations.gtf", validate_gtf=True)
lenient = pg.GffReader("annotations.gtf", skip_invalid_lines=True, validate_gtf=True)
```

::::

:::::

## Loading into a grove

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

```cpp
gst::grove<gdt::interval, std::string> g(100);
for (const auto& e : gio::gff_reader("annotations.gff3.gz")) {
    if (e.type != "gene") continue;
    g.insert_data(e.seqid, gdt::interval(e.start - 1, e.end - 1),
                  e.get_gene_id().value_or(e.type), gst::sorted);
}
```

::::

::::{tab-item} {{ py_tab }}
:sync: py

`GffGrove.insert(index, entry)` derives the 0-based closed key from the 1-based record:

```python
g = pg.GffGrove(100)
for e in pg.GffReader("annotations.gff3.gz"):
    if e.type == "gene":
        g.insert(e.seqid, e)
```

::::

:::::