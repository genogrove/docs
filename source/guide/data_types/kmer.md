# K-mer

A **point** key holding a DNA sequence of at most 32 bases, packed two bits per base (`A=00`,
`C=01`, `G=10`, `T=11`) into one 64-bit integer together with its length `k`. Two k-mers "overlap"
only when they are **identical**, so in a grove keyed by `kmer` `intersect` is an exact lookup
(membership, counts) and `flanking` returns the nearest k-mers on either side in sort order.

## Building a k-mer

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

```cpp
#include <genogrove/data_type/kmer.hpp>

namespace gdt = genogrove::data_type;

gdt::kmer k1{"ACGT"};                 // from a sequence (case-insensitive)
gdt::kmer k2{0b00011011, 4};          // from an encoding and k — the same 4-mer

k1 == k2;                             // true
gdt::kmer::overlaps(k1, k2);          // true — identical sequence
k1.to_string();                       // "ACGT"
k1.get_k();                           // 4
gdt::kmer::is_valid("ACGN");          // false — N is not a base
```

The sequence constructor throws `std::invalid_argument` for a base outside `ACGT` (any case) or a
length over 32; the encoding constructor masks the encoding to `k` bases and throws if `k > 32`. A
default-constructed `kmer` is the empty 0-mer.

::::

::::{tab-item} {{ py_tab }}
:sync: py

```python
import pygenogrove as pg

k1 = pg.Kmer("ACGT")                  # from a sequence (case-insensitive)
k2 = pg.Kmer(0b00011011, 4)           # from an encoding and k — the same 4-mer

k1 == k2                              # True
pg.Kmer.overlaps(k1, k2)              # True — identical sequence
str(k1), k1.k, len(k1), k1.encoding   # "ACGT", 4, 4, 27
pg.Kmer.is_valid("ACGN")              # False — N is not a base
```

```python
Kmer(sequence: str)
Kmer(encoding: int, k: int)           # encoding is masked to k bases
```

The sequence constructor raises `ValueError` for a base outside `ACGT` or a length over 32; the
encoding constructor masks the encoding to `k` bases and raises `ValueError` for `k` in 33–255
(a `k` above 255 does not fit the 8-bit parameter and is rejected earlier with `TypeError`).

::::

:::::

## Ordering

K-mers sort by `k` first, then by encoding, so every 4-mer sorts before every 5-mer and k-mers of
one length sort as their packed integers (which is alphabetical in `A < C < G < T`). Equality
compares both fields.

## The kmer type

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

`gdt::kmer` — a `uint64_t` encoding and a `uint8_t` length. It has no setters.

Methods:

- `get_encoding()`, `get_k()`
- `static overlaps(a, b)` — same `k` and same encoding
- `static aggregate(a, b)` — the greater of the two in sort order
- `static is_valid(sequence)` — `constexpr` validity check (bases and length)
- `static encode_base(c)`, `static decode_base(bits)` — single-base conversions; `BASE_MASK`
  (`0x03`) isolates one base from an encoding
- `to_string()` — the sequence
- `serialize(os)`, `static deserialize(is)` — binary persistence
- `max_k` — `static constexpr uint8_t`, 32
- `<`, `>`, `==` — ordering as above
- `std::hash<kmer>` — specialised, so it works in unordered containers and as a `registry` key

::::

::::{tab-item} {{ py_tab }}
:sync: py

`Kmer` — attributes `encoding`, `k` (read-only); `len(kmer)` is `k`. `Kmer` is immutable — there
are no setters.

Methods:

- `Kmer.overlaps(a, b)` — static; same `k` and same encoding
- `Kmer.is_valid(sequence)` — static validity check (bases and length)
- `Kmer.max_k` — class attribute, 32
- `<`, `<=`, `>`, `>=`, `==`, `hash()`, `str()`, `repr()` — ordering as above

::::

:::::

## In a grove

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

```cpp
#include <genogrove/structure/grove/grove.hpp>
#include <genogrove/data_type/kmer.hpp>

namespace gdt = genogrove::data_type;
namespace gst = genogrove::structure;

gst::grove<gdt::kmer, int> counts(100);
counts.insert_data("reads", gdt::kmer{"ACGT"}, 3);

auto hit = counts.intersect(gdt::kmer{"ACGT"}, "reads");     // membership: 1 key
hit.get_keys().front()->get_data();                           // 3
```

::::

::::{tab-item} {{ py_tab }}
:sync: py

```python
km = pg.KmerGrove(100)
km.insert("reads", pg.Kmer("ACGT"), {"count": 3})

list(km.intersect(pg.Kmer("ACGT"), "reads"))[0].data    # {'count': 3}
```

`KmerGrove` has the same surface as `Grove` (payloads, graph edges, serialization) with `Kmer` keys —
see {doc}`/guide/grove/index`.

::::

:::::