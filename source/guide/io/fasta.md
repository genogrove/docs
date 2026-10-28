# FASTA / FASTQ Files

Two tools cover sequence files: a **streaming reader** that yields every record of a FASTA or FASTQ
file in order (reading one record at a time, never the whole file at once), and an **index** that
fetches one region or one whole sequence from a FASTA file without reading the rest. The index relies
on a `.fai` file — the same small lookup table `samtools faidx` writes — created next to the FASTA on
first use. FASTA files hold named sequences; FASTQ files hold named sequences plus a quality string,
one character of base-call quality for each base. Sequences are named records, not
intervals, so neither feeds a {term}`grove` directly; the index is what you reach for once a grove
query (see {doc}`/guide/grove/querying`) has given you coordinates.

The snippets read `reads.fq.gz` (streaming) and `genome.fa` (index); substitute your own files.
Any FASTA or FASTQ file works for the streaming snippets; the index snippets need a FASTA file that
has a sequence named `chr1`.
Installation and how to compile the C++ examples: {doc}`/guide/installation`.

## Streaming records

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

```cpp
#include <genogrove/io/fasta_reader.hpp>
#include <iostream>

namespace gio = genogrove::io;

int main() {
    gio::fasta_reader reader("reads.fq.gz");

    try {
        for (const auto& rec : reader) {
            std::cout << rec.name << " " << rec.sequence.size() << " bp\n";
            // quality is an optional: `if (rec.quality)` tests whether it is present, `*` reads it
            if (rec.quality) std::cout << "  " << *rec.quality << "\n";   // FASTQ only
        }
    } catch (const std::runtime_error& e) {              // the exception a read failure raises
        std::cerr << "Parse error: " << e.what() << "\n";
    }
    return 0;
}
```

The constructor's signature and options (a declaration, not runnable code):

```cpp
explicit fasta_reader(const std::filesystem::path& path);                                // default options
fasta_reader(const std::filesystem::path& path, const fasta_reader_options& options);
struct fasta_reader_options { bool skip_empty_sequences = false; };
```

FASTA versus FASTQ is detected per record (`>` or `@` header), so mixed files work. There is no
lenient mode: a truncated quality string or an I/O error throws.

::::

::::{tab-item} {{ py_tab }}
:sync: py

```python
import pygenogrove as pg

for rec in pg.FastaReader("reads.fq.gz"):
    print(rec.name, len(rec), "bp")           # len(rec): the sequence length
    if rec.is_fastq():                        # True when a quality string is present
        print(" ", rec.quality)
```

The constructor's signature (not runnable code):

```python
FastaReader(path: str, skip_empty_sequences: bool = False)
```

FASTA versus FASTQ is detected per record, so mixed files work. There is no lenient mode: a
truncated quality string or an I/O error raises `RuntimeError`.

::::

:::::

## The sequence record

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

`gio::fasta_entry`:

| Field | Type |
|---|---|
| `name` | `std::string` — header text up to the first whitespace |
| `comment` | `std::string` — rest of the header line, empty if none |
| `sequence` | `std::string` |
| `quality` | `std::optional<std::string>` (a string that may be absent) — set for FASTQ, `nullopt` (absent) for FASTA |

A record can also be built by hand: `fasta_entry()` or `fasta_entry(name, sequence)`. There is no
`is_fastq()` on the C++ record — test `rec.quality` instead — and the length is
`rec.sequence.size()`.

::::

::::{tab-item} {{ py_tab }}
:sync: py

`FastaEntry`:

| Attribute | Type |
|---|---|
| `name` | `str` — header text up to the first whitespace |
| `comment` | `str` — rest of the header line, empty if none |
| `sequence` | `str` |
| `quality` | `Optional[str]` — set for FASTQ, `None` for FASTA |

Constructors: `FastaEntry()` and `FastaEntry(name, sequence)`. `repr(rec)` shows the record.

Methods:

- `is_fastq()` — `True` when a quality string is present
- `len(rec)` — the sequence length

::::

:::::

## Random access with an index

The index opens a FASTA file and loads its `.fai`, creating it on first use (the directory must be
writable then). Fetches are **0-based half-open** `[start, end)` — `end` is one past the last
base, as in BED and BAM — and return the bases as a string.

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

```cpp
#include <genogrove/io/fasta_index.hpp>
#include <iostream>

namespace gio = genogrove::io;

int main() {
    gio::fasta_index fasta("genome.fa");

    std::string promoter = fasta.fetch("chr1", 1000, 2000);   // bases [1000, 2000)
    std::string chrM     = fasta.fetch("chrM");                // whole sequence
    std::cout << promoter << "\n" << chrM << "\n";

    // sequences are numbered 0 .. sequence_count() - 1
    for (size_t i = 0; i < fasta.sequence_count(); ++i) {
        auto name = fasta.sequence_name(i);                    // auto: the compiler picks the type
        std::cout << name << ": " << fasta.sequence_length(name) << " bp\n";
    }
    std::cout << fasta.has_sequence("chrUn") << "\n";          // 0 (false)
    std::cout << fasta.sequence_count() << " sequences\n";
    return 0;
}
```

`fetch`, `sequence_name` and `sequence_length` throw a `std::out_of_range` {term}`exception` for an
unknown name, a number out of range, or an invalid region (`start >= end`, or beyond htslib's
coordinate limit); `std::runtime_error` means the htslib fetch itself failed. `fasta_index` is
non-copyable and movable: you can hand it to another owner but not duplicate it. Do not share one
`fasta_index` between threads unless you protect it with your own lock (see
{doc}`/guide/thread_safety`).

::::

::::{tab-item} {{ py_tab }}
:sync: py

```python
import pygenogrove as pg

fa = pg.FastaIndex("genome.fa")

print(fa.fetch("chr1", 1000, 2000))      # bases [1000, 2000)
print(fa.fetch("chrM"))                  # whole sequence

for name in fa.names():
    print(name, fa.sequence_length(name))
print("chrUn" in fa)                     # False: is the name present?
print(len(fa), "sequences")              # number of sequences
```

Unknown names and invalid regions raise `IndexError`. One handle is safe to use from several
threads at once: `fetch` calls on it take turns while the {term}`GIL` is released, and the metadata
getters need no lock (see {doc}`/guide/thread_safety`).

::::

:::::

## Pairing fetches with grove coordinates

Grove keys are **{term}`0-based closed`** and GFF records are **1-based closed**, while `fetch` is
0-based half-open — so the end (and for GFF the start) shifts by one. In the snippets `key` is the
{term}`key handle <key>` a grove query returns (see {doc}`/guide/grove/querying`) and `entry` a GFF
record ({doc}`gff`). The chromosome is not part of the key's value; pass the chromosome name you
queried (the grove {term}`index` name, which is a different thing from the FASTA `.fai` index).

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

Fragments: `fasta` is the index from above, `g` a grove you filled earlier (see
{doc}`/guide/grove/loading_data`), `key` one of its hits — a {term}`pointer`, hence `->` — and
`chrom` the chromosome you queried.

```cpp
std::string chrom = "chr1";
auto hits = g.intersect(gdt::interval{100, 200}, chrom);
auto* key = hits.get_keys().front();             // assumes at least one hit

// From a grove key (0-based closed [start, end]) — add 1 to end
std::string seq = fasta.fetch(chrom, key->get_value().get_start(), key->get_value().get_end() + 1);

// From a GFF record (1-based closed) — shift start down by one
std::string seq2 = fasta.fetch(entry.seqid, entry.start - 1, entry.end);
```

The chromosome is not part of an `interval`, so it has to come from your query.

::::

::::{tab-item} {{ py_tab }}
:sync: py

Fragments: `fa` is the index from above, `g` a grove you filled earlier (see
{doc}`/guide/grove/loading_data`) and `key` one of its hits; `key.value` is the stored
`GenomicCoordinate`.

```python
chrom = "chr1"
key = list(g.intersect(pg.GenomicCoordinate("*", 100, 200), chrom))[0]   # assumes at least one hit

# From a grove key (0-based closed [start, end]) — add 1 to end
gc = key.value
seq = fa.fetch(chrom, gc.start, gc.end + 1)

# From a GFF record (1-based closed) — shift start down by one
seq2 = fa.fetch(entry.seqid, entry.start - 1, entry.end)
```

The chromosome is not part of a `GenomicCoordinate`, so it has to come from your query.

::::

:::::
