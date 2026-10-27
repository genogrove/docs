# FASTA / FASTQ Files

Two tools cover sequence files: a **streaming reader** that yields every record of a FASTA or FASTQ
file in order, and an **index** that fetches one region or one whole sequence from a FASTA file
without scanning it, using a `.fai` index that is created on first use. Sequences are named records,
not intervals, so neither feeds a grove directly; the index is what you reach for once a grove query
has given you coordinates.

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
            if (rec.quality) std::cout << "  " << *rec.quality << "\n";   // FASTQ only
        }
    } catch (const std::runtime_error& e) {
        std::cerr << "Parse error: " << e.what() << "\n";
    }
    return 0;
}
```

```cpp
fasta_reader(const std::string& path, fasta_reader_options options = {});
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
    print(rec.name, len(rec), "bp")
    if rec.is_fastq():
        print(" ", rec.quality)
```

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
| `quality` | `std::optional<std::string>` — set for FASTQ, `nullopt` for FASTA |

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

`is_fastq()` reports whether a quality string is present; `len(rec)` is the sequence length. A record
can be built by hand with `FastaEntry(name, sequence)`.

::::

:::::

## Random access with an index

The index opens a FASTA file and loads its `.fai`, creating it on first use (the directory must be
writable then). Fetches are **0-based half-open** `[start, end)` — the BED/BAM convention — and
return the bases as a string.

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

```cpp
#include <genogrove/io/fasta_index.hpp>

gio::fasta_index fasta("genome.fa");

std::string promoter = fasta.fetch("chr1", 1000, 2000);   // bases [1000, 2000)
std::string chrM     = fasta.fetch("chrM");                // whole sequence

for (size_t i = 0; i < fasta.sequence_count(); ++i) {
    auto name = fasta.sequence_name(i);
    std::cout << name << ": " << fasta.sequence_length(name) << " bp\n";
}
fasta.has_sequence("chrUn");                               // false
```

`fetch`, `sequence_name` and `sequence_length` throw `std::out_of_range` for an unknown name, an
index out of range, or an invalid region (`start >= end`, or beyond htslib's coordinate limit);
`std::runtime_error` means the htslib fetch itself failed. `fasta_index` is non-copyable and
movable.

::::

::::{tab-item} {{ py_tab }}
:sync: py

```python
fa = pg.FastaIndex("genome.fa")

fa.fetch("chr1", 1000, 2000)      # bases [1000, 2000)
fa.fetch("chrM")                  # whole sequence

for name in fa.names():
    print(name, fa.sequence_length(name))
"chrUn" in fa, len(fa)            # has_sequence / sequence_count
```

Unknown names and invalid regions raise `IndexError`. One handle may be shared between threads:
`fetch` calls are serialized by a per-handle lock while the GIL is released; the metadata getters are
lock-free (see {doc}`/guide/thread_safety`).

::::

:::::

## Pairing fetches with grove coordinates

Grove keys are **0-based closed** and GFF records are **1-based closed**, while `fetch` is 0-based
half-open — so the end (and for GFF the start) shifts by one.

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

```cpp
// From a grove key (0-based closed [start, end]) — add 1 to end
std::string seq = fasta.fetch(chrom, key->get_value().get_start(), key->get_value().get_end() + 1);

// From a GFF record (1-based closed) — shift start down by one
std::string seq2 = fasta.fetch(entry.seqid, entry.start - 1, entry.end);
```

The chromosome is not part of an `interval`; pass the grove index name you queried.

::::

::::{tab-item} {{ py_tab }}
:sync: py

```python
# From a grove key (0-based closed [start, end]) — add 1 to end
gc = key.value
seq = fa.fetch("chr1", gc.start, gc.end + 1)

# From a GFF record (1-based closed) — shift start down by one
seq2 = fa.fetch(entry.seqid, entry.start - 1, entry.end)
```

The chromosome is not part of a `GenomicCoordinate`; pass the grove index name you queried.

::::

:::::