# BED Files

BED files list genomic intervals with up to nine optional columns. The reader accepts BED3 through
BED12 and files that **mix** record widths: a shorter line after a longer one simply has the extra
fields absent (nothing carries over from the previous record). Plain and gzip/bgzip-compressed
(`.gz`) files are detected automatically. Coordinates are **0-based half-open** `[start, end)`;
convert with `end - 1` for a {term}`grove` {term}`key` (see {doc}`index`).

The snippets read `genes.bed.gz`; substitute any BED file. Installation and how to compile the C++
examples: {doc}`/guide/installation`.

## Reading a BED file

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

```cpp
#include <genogrove/io/bed_reader.hpp>
#include <iostream>

namespace gio = genogrove::io;

int main() {
    gio::bed_reader reader("genes.bed.gz");

    try {
        for (const auto& entry : reader) {
            std::cout << entry.chrom << ":" << entry.start << "-" << entry.end;
            // optional fields: `if (field)` tests whether the column was present,
            // `*field` reads it, `field->member` reads one part of it
            if (entry.name)   std::cout << " " << *entry.name;      // BED4+
            if (entry.strand) std::cout << " " << *entry.strand;    // BED6+
            if (entry.blocks) std::cout << " (" << entry.blocks->count << " blocks)";   // BED12
            std::cout << "\n";
        }
    } catch (const std::runtime_error& e) {              // the exception a bad line raises
        std::cerr << "Parse error: " << e.what() << "\n";
    }
    return 0;
}
```

The constructor's signature and options (a declaration, not runnable code):

```cpp
bed_reader(const std::string& path, bed_reader_options options = {});   // = {}: defaults
struct bed_reader_options {
    bool skip_invalid_lines = false;   // skip malformed lines instead of throwing
    std::string region = "";           // tabix region, see below
};
```

`region` restricts reading to one locus of an indexed `.gz` file — see {doc}`region_access`.

::::

::::{tab-item} {{ py_tab }}
:sync: py

```python
import pygenogrove as pg

for entry in pg.BedReader("genes.bed.gz"):
    line = f"{entry.chrom}:{entry.start}-{entry.end}"
    if entry.name is not None:   line += f" {entry.name}"          # BED4+
    if entry.strand is not None: line += f" {entry.strand}"        # BED6+
    if entry.blocks is not None: line += f" ({entry.blocks.count} blocks)"   # BED12
    print(line)
```

The constructor's signature (not runnable code):

```python
BedReader(path: str, skip_invalid_lines: bool = False, region: str = "")
```

`skip_invalid_lines=True` skips malformed lines instead of raising; `region` restricts reading to
one locus of an indexed `.gz` file — see {doc}`region_access`.

::::

:::::

## The BED record

Required fields are always present; the rest are optional and absent (`None` in Python, an empty
optional in C++) when the line did not have them.

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

`gio::bed_entry`:

| Field | Type | Column |
|---|---|---|
| `chrom` | `std::string` | 1 |
| `start`, `end` | `size_t` (unsigned integer; 0-based half-open) | 2, 3 |
| `name` | `std::optional<std::string>` | 4 |
| `score` | `std::optional<int>` | 5 |
| `strand` | `std::optional<char>` (`'+'` / `'-'` / `'.'`) | 6 |
| `thickness` | `std::optional<thick_info>` (`start`, `end`) | 7, 8 |
| `item_rgb` | `std::optional<rgb_color>` (`red`, `green`, `blue`, 0–255) | 9 |
| `blocks` | `std::optional<block_info>` (`count`, `sizes`, `starts`) | 10–12 |

`std::optional<T>` is "a `T` that may be absent": test it like a bool, then read it with `*` (or
`->` for a member of it).

A record can also be built by hand — `bed_entry()` or `bed_entry(chrom, start, end)`, then set the
optional fields — and all fields are plain members you can read and assign.

Methods:

- `serialize(os)`, `static deserialize(is)` — binary {term}`serialization`, so a
  `grove<gdt::interval, gio::bed_entry>` (a grove whose {term}`payload` is the whole record) can be
  saved to disk directly; this is what the {term}`CLI`'s `idx` command writes (see {doc}`/cli`)

Otherwise the fields are the record: there is no coordinate helper, so build the grove key with
`gdt::interval(e.start, e.end - 1)`.

::::

::::{tab-item} {{ py_tab }}
:sync: py

`BedEntry` — attributes are read/write:

| Attribute | Type | Column |
|---|---|---|
| `chrom` | `str` | 1 |
| `start`, `end` | `int` (0-based half-open) | 2, 3 |
| `name` | `Optional[str]` | 4 |
| `score` | `Optional[int]` | 5 |
| `strand` | `Optional[str]`, one of `'+'` / `'-'` / `'.'` | 6 |
| `thickness` | `Optional[ThickInfo]` (`start`, `end`) | 7, 8 |
| `item_rgb` | `Optional[RgbColor]` (`red`, `green`, `blue`, 0–255) | 9 |
| `blocks` | `Optional[BlockInfo]` (`count`, `sizes`, `starts`) | 10–12 |

Constructors: `BedEntry()` and `BedEntry(chrom, start, end)`; set the optional attributes
afterwards. `repr(entry)` shows the record. Assigning an empty or multi-character `strand` raises
`ValueError`, `None` clears it. List fields (`blocks.sizes`, `blocks.starts`) are returned and
assigned by copy, so `entry.blocks.sizes.append(1)` does not change the record — build a new list
and assign it.

There is no `to_coordinate()` on `BedEntry`: `BedGrove.insert(index, entry)` derives the grove key
from the record, which becomes the payload (see {doc}`/guide/grove/loading_data`).

::::

:::::

## Loading into a grove

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

Convert the half-open end:

```cpp
#include <genogrove/io/bed_reader.hpp>
#include <genogrove/structure/grove/grove.hpp>
#include <genogrove/data_type/interval.hpp>

namespace gio = genogrove::io;
namespace gdt = genogrove::data_type;
namespace gst = genogrove::structure;

int main() {
    gst::grove<gdt::interval, std::string> g(100);   // interval keys, string payloads;
                                                     // 100 = tree order, a good default
    gio::bed_reader reader("genes.bed.gz");
    for (const auto& e : reader) {
        // payload: the name column, or "unnamed" when the line had none
        g.insert_data(e.chrom, gdt::interval(e.start, e.end - 1), e.name.value_or("unnamed"));
    }
    return 0;
}
```

If you know the file is position-sorted, add `gst::sorted` as the last argument for the
constant-time ({term}`O(1) <O(log n), O(n)>`) append path — but only then; the
{term}`sorted insert` does not check (see {doc}`/guide/grove/inserting`). For large files collect
per chromosome and {term}`bulk-insert <bulk insert>` — see {doc}`/guide/grove/loading_data`.

::::

::::{tab-item} {{ py_tab }}
:sync: py

`BedGrove.insert(index, entry)` derives the {term}`0-based closed` key from the record, so no
conversion is needed:

```python
import pygenogrove as pg

g = pg.BedGrove(100)                                     # 100 = tree order, a good default
for e in pg.BedReader("genes.bed.gz"):
    g.insert(e.chrom, e)

# or per chromosome in bulk
g.insert_bulk("chr1", [e for e in pg.BedReader("genes.bed.gz") if e.chrom == "chr1"])
```

Sortedness: `insert` finds the right place itself, so the file need not be sorted.
`insert_bulk(index, entries)` sorts the list for you; pass `presorted=True` only when the list is
already in ascending order — like C++ `gst::sorted`, that path does not check. The single-record
fast path `insert_sorted(index, coord, data)` takes an explicit coordinate and payload, not a bare
entry. See {doc}`/guide/grove/loading_data` for the typed groves.

::::

:::::
