# BED Files

BED files list genomic intervals with up to nine optional columns. The reader accepts BED3 through
BED12 and files that **mix** record widths; optional fields are reset on every record, so a BED6 line
after a BED12 line carries no stale block or colour data. Coordinates are **0-based half-open**
`[start, end)`; convert with `end - 1` for a grove key (see {doc}`index`).

## Reading a BED file

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

```cpp
#include <genogrove/io/bed_reader.hpp>
#include <iostream>

namespace gio = genogrove::io;

int main() {
    gio::bed_reader reader("example.bed.gz");

    try {
        for (const auto& entry : reader) {
            std::cout << entry.chrom << ":" << entry.start << "-" << entry.end;
            if (entry.name)   std::cout << " " << *entry.name;      // BED4+
            if (entry.strand) std::cout << " " << *entry.strand;    // BED6+
            if (entry.blocks) std::cout << " (" << entry.blocks->count << " blocks)";   // BED12
            std::cout << "\n";
        }
    } catch (const std::runtime_error& e) {
        std::cerr << "Parse error: " << e.what() << "\n";
    }
    return 0;
}
```

```cpp
bed_reader(const std::string& path, bed_reader_options options = {});
struct bed_reader_options {
    bool skip_invalid_lines = false;   // skip malformed lines instead of throwing
    std::string region = "";           // tabix region, see region_access
};
```

::::

::::{tab-item} {{ py_tab }}
:sync: py

```python
import pygenogrove as pg

for entry in pg.BedReader("example.bed.gz"):
    line = f"{entry.chrom}:{entry.start}-{entry.end}"
    if entry.name is not None:   line += f" {entry.name}"          # BED4+
    if entry.strand is not None: line += f" {entry.strand}"        # BED6+
    if entry.blocks is not None: line += f" ({entry.blocks.count} blocks)"   # BED12
    print(line)
```

```python
BedReader(path: str, skip_invalid_lines: bool = False, region: str = "")
```

::::

:::::

## The BED record

Required fields are always present; the rest are optional and absent (`std::nullopt` / `None`) when
the line did not have them.

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

`gio::bed_entry`:

| Field | Type | Column |
|---|---|---|
| `chrom` | `std::string` | 1 |
| `start`, `end` | `size_t` (0-based half-open) | 2, 3 |
| `name` | `std::optional<std::string>` | 4 |
| `score` | `std::optional<int>` | 5 |
| `strand` | `std::optional<char>` (`'+'` / `'-'` / `'.'`) | 6 |
| `thickness` | `std::optional<thick_info>` (`start`, `end`) | 7, 8 |
| `item_rgb` | `std::optional<rgb_color>` (`red`, `green`, `blue`) | 9 |
| `blocks` | `std::optional<block_info>` (`count`, `sizes`, `starts`) | 10–12 |

Methods:

- `serialize(os)`, `static deserialize(is)` — binary persistence, so a
  `grove<gdt::interval, gio::bed_entry>` can be saved directly (this is what the CLI's `idx` writes)

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
assigned by copy.

There is no `to_coordinate()` on `BedEntry`: `BedGrove.insert(index, entry)` derives the grove key
from the record (see {doc}`/guide/grove/loading_data`).

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

gst::grove<gdt::interval, std::string> g(100);
gio::bed_reader reader("genes.bed.gz");
for (const auto& e : reader) {
    g.insert_data(e.chrom, gdt::interval(e.start, e.end - 1), e.name.value_or("unnamed"));
}
```

If you know the file is position-sorted, add `gst::sorted` as the last argument for the O(1) append
path — but only then; the sorted path does not check (see {doc}`/guide/grove/inserting`). For large
files collect per chromosome and bulk-insert — see {doc}`/guide/grove/loading_data`.

::::

::::{tab-item} {{ py_tab }}
:sync: py

`BedGrove.insert(index, entry)` derives the 0-based closed key from the record, so no conversion
is needed:

```python
g = pg.BedGrove(100)
for e in pg.BedReader("genes.bed.gz"):
    g.insert(e.chrom, e)

# or per chromosome in bulk
g.insert_bulk("chr1", [e for e in pg.BedReader("genes.bed.gz") if e.chrom == "chr1"])
```

See {doc}`/guide/grove/loading_data` for the typed groves.

::::

:::::