# BED Files

BED files list genomic intervals with up to nine optional columns. The reader accepts BED3 through
BED12 and files that **mix** record widths: a shorter line after a longer one simply has the extra
fields absent (nothing carries over from the previous record). Plain and gzip/bgzip-compressed
(`.gz`) files are detected automatically. Coordinates are **0-based half-open** `[start, end)`;
convert with `end - 1` for a {term}`grove` {term}`key` (see {doc}`index`).

The snippets read `genes.bed.gz`; substitute any BED file. If you have none, save these three tab-separated
lines as `genes.bed` and use that name:

```text
chr1	100	200	geneA	0	+
chr1	300	400	geneB	0	-
chr2	50	150	geneC	0	+
```

Installation and how to compile the C++ examples: {doc}`/guide/installation`.

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
explicit bed_reader(const std::filesystem::path& path);                              // default options
bed_reader(const std::filesystem::path& path, const bed_reader_options& options);
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

try:
    for entry in pg.BedReader("genes.bed.gz"):
        line = f"{entry.chrom}:{entry.start}-{entry.end}"
        if entry.name is not None:   line += f" {entry.name}"          # BED4+
        if entry.strand is not None: line += f" {entry.strand}"        # BED6+
        if entry.blocks is not None: line += f" ({entry.blocks.count} blocks)"   # BED12
        print(line)
except RuntimeError as e:                         # the exception a bad line raises
    print("Parse error:", e)
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

`Optional[str]` means "a `str`, or `None` when the column is absent": test it with `if entry.name:`
or `is not None`. Whole records saved in a `BedGrove` go to disk with `serialize` (see
{doc}`/guide/serialization/index`).

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

The grove, its {term}`order` (the `100`) and `insert_data` are explained in {doc}`/guide/grove/index`.
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

If the file is sorted by start and then by end, add `gst::sorted` as the last argument for the
faster append path. Sorting by start alone is not enough: two records with the same start must come
in order of their end. Use this tag only when you know the file has that order. The
{term}`sorted insert` does not check, and a wrong order silently breaks the tree (see
{doc}`/guide/grove/inserting`). For large files collect per chromosome and {term}`bulk-insert <bulk insert>` — see {doc}`/guide/grove/loading_data`.

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

# Alternative to the loop above: bulk insert into a NEW grove, one chromosome at a time
g = pg.BedGrove(100)
g.insert_bulk("chr1", [e for e in pg.BedReader("genes.bed.gz") if e.chrom == "chr1"])
```

The C++ example stores the name column as payload; a `BedGrove` stores the whole `BedEntry`, so the
name is still there after a query, as `hit.data.name` for each hit `hit` of the result. The bulk-insert variant above shows `chr1` only, as
one chromosome of the loop.

Sortedness: `insert` finds the right place itself, so the file need not be sorted.
`insert_bulk(index, entries)` sorts the list you give it, but it only appends to the index. If the
index already holds keys, every new key must be greater than all existing keys, whatever the value of
`presorted`. The code does not check this, and a wrong order silently breaks the tree. So use
`insert_bulk` on an empty index, such as the `chr1` index of a new grove. Pass `presorted=True` only
when the list is already ordered by start and then end; that path skips the sort. The single-record
fast path `insert_sorted(index, coord, data)` takes an explicit coordinate and payload, not a bare
entry. See {doc}`/guide/grove/loading_data` for the typed groves.

::::

:::::
