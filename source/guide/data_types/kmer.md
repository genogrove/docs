# K-mer

A **point** {term}`key type` holding a DNA sequence of at most 32 bases. Each base takes two bits
(`A=00`, `C=01`, `G=10`, `T=11`), and the bits of all bases form one 64-bit integer, the *encoding*.
The key also stores the length `k`. Two
{term}`k-mers <k-mer>` "{term}`overlap`" only when they are **identical**, so in a {term}`grove` keyed
by `kmer` `intersect` is an exact lookup (membership, counts) and {term}`flanking` returns the nearest
k-mers on either side in sort order.

## Building a k-mer

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

```cpp
#include <genogrove/data_type/kmer.hpp>

namespace gdt = genogrove::data_type;

gdt::kmer k1{"ACGT"};                 // from a sequence (case-insensitive)
gdt::kmer k2{0b00011011, 4};          // from an encoding and k — the same 4-mer
                                      // (0b… is a binary literal: 00 01 10 11 = A C G T)

k1 == k2;                             // true
gdt::kmer::overlaps(k1, k2);          // true — identical sequence
k1.to_string();                       // "ACGT"
k1.get_k();                           // 4
gdt::kmer::is_valid("ACGN");          // false — N is not a base
```

The comments show what each line evaluates to; the lines compute the value without printing it, so
wrap one in `std::cout << ... << '\n';` to see it. The sequence constructor throws a
`std::invalid_argument` {term}`exception` for a base outside `ACGT` (any case) or a length over 32.
The encoding constructor keeps only the lowest `2k` bits and throws if `k > 32`. A
default-constructed `kmer` (`gdt::kmer{}`) is the empty 0-mer.

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

The comments show what each line evaluates to; in an interactive Python session each line prints its
result (`0b…` is a binary literal: `00 01 10 11` = `A C G T`). Signatures (for reference, not to
paste):

```python
Kmer(sequence: str)
Kmer(encoding: int, k: int)           # encoding is masked to k bases
```

The sequence constructor raises a `ValueError` {term}`exception` for a base outside `ACGT` or a
length over 32. `Kmer(encoding, k)` keeps only the lowest `2k` bits and raises `ValueError` if `k`
is above 32. A `k` above 255 does not fit the 8-bit parameter and raises `TypeError`.

::::

:::::

## Ordering

K-mers sort by `k` first, then by encoding, so every 4-mer sorts before every 5-mer and k-mers of
one length sort as their packed integers (which is alphabetical in `A < C < G < T`). Equality
compares both fields. For example, `AC` sorts before `AAA`, because 2 is less than 3.

## The kmer type

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

`gdt::kmer` — a `uint64_t` encoding (64-bit unsigned integer) and a `uint8_t` length (8-bit unsigned
integer). It has no setters.

Methods:

- `get_encoding()`, `get_k()`
- `static overlaps(a, b)` — same `k` and same encoding
- `static aggregate(a, b)` — the greater of the two in sort order
- `static is_valid(sequence)` — `constexpr` check that every character is a base `A`, `C`, `G` or
  `T` (either case; usable at compile time). It does not check the length: a valid sequence of more
  than 32 bases passes this check and then fails in the constructor
- `static encode_base(c)`, `static decode_base(bits)` — single-base conversions; `BASE_MASK`
  (`0x03`, binary `11`) isolates one base from an encoding
- `to_string()` — the sequence
- `serialize(os)`, `static deserialize(is)` — binary persistence ({term}`serialization`)
- `max_k` — `static constexpr uint8_t` (a compile-time constant), 32
- `<`, `>`, `==` — ordering as above
- `std::hash<kmer>` — specialised (see {doc}`index`), so it works in unordered containers and as a
  {term}`registry` key

::::

::::{tab-item} {{ py_tab }}
:sync: py

`Kmer` — attributes `encoding`, `k` (read-only); `len(kmer)` is `k`. `Kmer` is immutable — there
are no setters.

Methods:

- `Kmer.overlaps(a, b)` — static; same `k` and same encoding
- `Kmer.is_valid(sequence)` — static check that every character is a base `A`, `C`, `G` or `T` (either case). It does not check the length: a valid sequence of more than 32 bases passes this check and then fails in the constructor
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

gst::grove<gdt::kmer, int> counts(100);                       // kmer keys, int payloads
counts.insert_data("reads", gdt::kmer{"ACGT"}, 3);            // "reads" is the index

auto hit = counts.intersect(gdt::kmer{"ACGT"}, "reads");     // membership: 1 key
hit.get_keys().front()->get_data();                           // 3
```

`"reads"` is the {term}`index`: in a k-mer grove it is simply the name of one tree, not a chromosome.
`100` is the tree {term}`order`, `int` the {term}`payload` type. `get_keys()` holds
{term}`key handles <key handle>` ({term}`pointers <pointer>`), hence the `->`.

::::

::::{tab-item} {{ py_tab }}
:sync: py

```python
import pygenogrove as pg

km = pg.KmerGrove(100)
km.insert("reads", pg.Kmer("ACGT"), {"count": 3})       # "reads" is the index

list(km.intersect(pg.Kmer("ACGT"), "reads"))[0].data    # {'count': 3}
```

`"reads"` is the {term}`index`: in a k-mer grove it is simply the name of one tree, not a chromosome.
`100` is the tree {term}`order`, the dict the {term}`payload`. `intersect` returns a
{term}`QueryResult`, hence the `list(...)`; `.data` on a {term}`Key <key handle>` is the payload.

`KmerGrove` has the same surface as `Grove` (payloads, graph edges, serialization) with `Kmer` keys —
see {doc}`/guide/grove/index`.

::::

:::::