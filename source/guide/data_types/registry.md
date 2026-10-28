# Registry

A {term}`registry` collapses the thousands of repeats of the same string in a dataset — chromosome
names, transcript or gene IDs, sample identifiers — into one small integer you store as a
{term}`grove` {term}`payload`, and gives the string back when you need it. For example, if a million
intervals each belong to a sample called `SampleA_liver`, you store the name once and the number `0`
a million times. This is called {term}`interning`: every distinct key gets one stable 4-byte ID, and
interning the same key again returns the existing ID.

## Getting the registry

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

`gdt::registry<Key, Tag = void, Payload = Key>` is a {term}`singleton`, one shared object per
combination of {term}`template` arguments (**process-wide singleton per template instantiation**):
`registry<std::string>::instance()` always returns the same object.

```cpp
#include <genogrove/data_type/registry.hpp>

namespace gdt = genogrove::data_type;

auto& reg = gdt::registry<std::string>::instance();
```

- `Key` — the identity that is deduplicated; must satisfy `registry_value` (see
  [Requirements on the key type](#requirements-on-the-key-type))
- `Tag` — a phantom type (a type used only as a label, holding no data) that separates pools of the
  same `Key` type (see [Separate pools](#separate-pools))
- `Payload` — what is stored against each ID; defaults to the key itself (see [Richer payloads](#richer-payloads))

::::

::::{tab-item} {{ py_tab }}
:sync: py

`Registry` is a process-wide {term}`singleton` (one shared object for the whole program) mapping a
string key to a payload that can be any JSON value (a dict, list, string, number or `None`):

```python
import pygenogrove as pg

r = pg.Registry.instance()
```

There is one pool, and one ID space, per process. Already covered: key prefixes keep unrelated names apart inside that one pool (see "Separate pools" below).

::::

:::::

## Interning and looking up

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

```cpp
// continuing from above: reg is the registry obtained from instance()
auto id1 = reg.intern("chr1");          // 0 — new
auto id2 = reg.intern("chr1");          // 0 — already present, same ID
auto id3 = reg.intern("chr2");          // 1

reg.find("chr3");                       // std::optional<id_type> (holds an ID or is empty): empty — not interned, nothing added
reg.find("chr1");                       // optional{0}
const std::string& name = reg.get(id1); // "chr1"

reg.size();                             // 2
reg.empty();                            // false
reg.contains(id1);                      // true
reg.contains(999);                      // false
```

The comments show what each line evaluates to; the lines compute the value without printing it. IDs
are `registry::id_type` (`uint32_t`, a 32-bit unsigned integer), handed out in insertion order from
0. `get(id)` with an unknown ID throws `std::out_of_range`.

Limit: `registry::null_id` (`UINT32_MAX`) is reserved and never returned, so a pool holds up to
`null_id` entries. `intern` throws a `std::runtime_error` {term}`exception` on the entry after that.

Store the ID in the grove instead of the string:

```cpp
#include <genogrove/structure/grove/grove.hpp>
#include <genogrove/data_type/interval.hpp>
// continuing from above: gdt and reg

namespace gst = genogrove::structure;

gst::grove<gdt::interval, gdt::registry<std::string>::id_type> g(100);   // payload type: the ID
g.insert_data("chr1", gdt::interval{100, 200}, reg.intern("SampleA_liver"));
```

`"chr1"` is the {term}`index` (the chromosome tree) and `100` the tree {term}`order`.

::::

::::{tab-item} {{ py_tab }}
:sync: py

```python
a = r.intern("chr1")          # 0 — new
b = r.intern("chr1")          # 0 — already present, same id
c = r.intern("chr2")          # 1

r.find("chr3")                # None — not interned, nothing added
r.find("chr1")                # 0
r.get(a)                      # "chr1"

r.size(), len(r)              # 2, 2
r.empty()                     # False
r.contains(a)                 # True
r.contains(999)               # False
```

The comments show what each line evaluates to; in an interactive Python session each line prints its
result. `len(r)` is the Python spelling of `size()`. IDs are handed out in insertion order from 0; `Registry.null_id` (`2**32 - 1`) is reserved.
`get(id)` with an unknown id raises an `IndexError` {term}`exception`.

Store the id in a grove payload instead of the string:

```python
# continuing from above: pg and r
g = pg.Grove(100)
g.insert("chr1", pg.GenomicCoordinate(".", 100, 200), {"sample": r.intern("SampleA_liver")})
```

C++ stores the bare ID as the payload; the Python example stores a dict that labels the ID (storing the
bare integer works as well). The C++ example uses an unstranded `interval`; Python has no `interval`
class, so the example uses the unstranded `GenomicCoordinate('.', start, end)`.

`"chr1"` is the {term}`index` (the chromosome tree) and `100` the tree {term}`order`.

::::

:::::

## Richer payloads

The key is what gets deduplicated; the **payload** is what `get` returns. By default they are the
same value. When identity is only part of a record — a gene ID keying a struct of gene fields — make
the payload the full record. Interning is **first-write-wins**: re-interning an existing key returns
its ID and drops the new payload.

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

Set the third template parameter and use the two-argument `intern(key, payload)`:

```cpp
// continuing from above: gdt
struct gene_info { std::string gene_name; std::string gene_biotype; };   // a plain record type
using gene_reg = gdt::registry<std::string, void, gene_info>;

auto id1 = gene_reg::instance().intern("ENSG001", {"FOO", "protein_coding"});
auto id2 = gene_reg::instance().intern("ENSG001", {"placeholder", ""});   // id1 == id2; payload kept from the first call
const gene_info& info = gene_reg::instance().get(id1);                    // {"FOO", "protein_coding"}
```

The one-argument `intern(value)` exists only when `Key == Payload` (`registry::key_is_payload`).
With this pattern the key is the identity, so `gene_info` needs no `operator==` or `std::hash`.

::::

::::{tab-item} {{ py_tab }}
:sync: py

The payload is any JSON-serializable value; the two-argument `intern(key, payload)` stores it:

```python
# continuing from above: r
id1 = r.intern("ENSG001", {"gene_name": "FOO", "gene_biotype": "protein_coding"})
id2 = r.intern("ENSG001", {"gene_name": "placeholder", "gene_biotype": ""})   # id1 == id2; payload kept from the first call
r.get(id1)                                          # {'gene_name': 'FOO', 'gene_biotype': 'protein_coding'}
```

The one-argument `intern(value)` stores the string as its own payload. Payloads must be **finite**
JSON: `float('nan')` / `float('inf')` at any nesting depth raise `ValueError` (the registry shares
the JSON encoder with `Grove`).

::::

:::::

## Separate pools

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

Two unrelated string pools in one binary — transcript IDs and annotation sources, say — would collapse
into the single `registry<std::string>` and share an ID space. Give each its own **tag**: a phantom
type (an empty type used only as a label) that costs nothing at runtime and appears nowhere in
storage or serialization.

```cpp
// continuing from above: gdt
using transcript_registry = gdt::registry<std::string, struct transcript_tag>;
using source_registry     = gdt::registry<std::string, struct source_tag>;

transcript_registry::instance().intern("ENST00000001");   // 0 in the transcript pool
source_registry::instance().intern("HAVANA");             // 0 in the source pool — separate
```

Each `(Key, Tag, Payload)` triple is its own singleton with its own ID space. The bare
`registry<std::string>` stays the right choice when one pool is what you want.

::::

::::{tab-item} {{ py_tab }}
:sync: py

Python has the one process-wide `Registry` with one ID space. The C++ tags that give each pool its own
ID space have no Python counterpart. What the prefixes give you is separate *names*, not separate IDs:
prefix the keys (`"tx:ENST00000001"`, `"src:HAVANA"`) so that two kinds of name cannot collide, and
remember that all IDs still come from the same sequence.

::::

:::::

## Requirements on the key type

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

`Key` must satisfy the `registry_value` concept (a C++20 *concept* is a named checklist of
requirements on a type): `std::equality_comparable` (it has `==`) and hashable through
`std::hash<Key>` (the standard hook that turns a value into the small integer a lookup table files it
under; see {doc}`index`). `std::string` and the integer types qualify, as do `genomic_coordinate`, `numeric`
and `kmer` (each ships a `std::hash` specialisation), so `registry<gdt::genomic_coordinate>` compiles
as-is. `interval` has no `std::hash` and cannot be a registry key without one. A custom type needs
both `operator==` and a `std::hash` specialisation.

::::

::::{tab-item} {{ py_tab }}
:sync: py

Keys are strings: any `str` works, and string keys cover the Python use cases (names and IDs). Already covered: the C++
non-string keys (`genomic_coordinate`, `numeric`, `kmer`) work in Python through their text form,
for example `r.intern(str(pg.GenomicCoordinate("+", 100, 200)))`.

::::

:::::

## Clearing

Clearing removes every entry and **invalidates every ID handed out so far** — payloads stored in a
grove that refer to them become meaningless. Do it between runs or tests, not while IDs are in use.

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

```cpp
// continuing from above: gdt and reg
reg.clear();                              // on the instance
gdt::registry<std::string>::reset();      // the same, as a static call (on the class, not an object)
```

`reset()` is only a shortcut for `instance().clear()`; use it where you have no object at hand, for
example in test set-up.

::::

::::{tab-item} {{ py_tab }}
:sync: py

```python
# continuing from above: pg and r
r.clear()                                 # on the instance
pg.Registry.reset()                       # the same, as a static call (on the class, not an object)
```

`reset()` is only a shortcut for `clear()` on the instance; use it where you have no object at hand,
for example in test set-up.

::::

:::::

## Persistence

A registry is saved and loaded ({term}`serialization`) separately from any grove. When grove payloads
hold registry IDs, write the registry **first** and read it back **first**, so the IDs resolve (see
{doc}`/guide/serialization/index`).

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

```cpp
#include <fstream>
// continuing from above: gdt and reg

{
    std::ofstream out("names.reg", std::ios::binary);           // a file stream, opened for bytes
    reg.serialize(out);
}                                                               // the closing brace closes and flushes the file

std::ifstream in("names.reg", std::ios::binary);
auto& restored = gdt::registry<std::string>::deserialize(in);   // replaces the singleton's contents
```

The two {term}`streams <stream>` are the file handles the registry writes to and reads from. The
file must be closed (here by the closing brace) before it is read back.

- Wire format (the byte layout in the file): with `Key == Payload`, a `uint64_t` (64-bit) count then
  each payload; otherwise `(key, payload)` pairs in ID order. Each value is written through
  `gdt::serializer<Payload>` (and `gdt::serializer<Key>` when they differ). A custom payload must
  therefore be {term}`trivially copyable` (a plain record of numbers) or provide its own
  `serialize` / `deserialize`. The `gene_info` above holds two `std::string` members, so it is not
  trivially copyable and needs its own `serialize` / `deserialize` members or a
  `serialization_traits` specialisation — see {doc}`/guide/serialization/index`.
- `deserialize` offers a {term}`strong exception guarantee`: it builds into temporaries and commits
  only after the whole stream has been read, so a truncated or corrupt stream leaves the singleton
  exactly as it was. It throws `std::runtime_error` for a count beyond `id_type` capacity
  (`"...entry count exceeds id_type capacity"`) and for a duplicate key (`"...duplicate key"`).

::::

::::{tab-item} {{ py_tab }}
:sync: py

```python
# continuing from above: pg and r
r.serialize("names.reg")                   # keys and JSON payloads
r2 = pg.Registry.deserialize("names.reg")  # loads into the singleton, replacing its contents
```

`deserialize` raises `RuntimeError` on a truncated or corrupt file and leaves the singleton as it was
(a {term}`strong exception guarantee`). Both calls {term}`release the GIL <GIL>`, so other Python
threads keep running during the file I/O.

::::

:::::

## Thread safety

If your program never runs more than one thread, skip this section. It says which calls are
{term}`thread-safe` (safe to make from several threads at once).

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

One internal `std::mutex` (a lock that lets one thread in at a time) per singleton.

- **Locked**: `intern()`, `find()`, `clear()`, `serialize()`, and the final commit of `deserialize()`
  (its I/O and parsing run unlocked, so a long load does not block `intern` / `find`). Because the
  commit **replaces** the contents, an `intern()` that ran while a `deserialize()` was in flight is
  discarded and its ID may now refer to a different loaded value — do not intern concurrently with a
  load, or repeat the interns after it.
- **Unlocked**: `get(id)`, `contains(id)`, `size()`, `empty()`. These are safe only while no writer
  (`intern`, `clear`, `reset`, `deserialize`) runs concurrently; an unlocked read overlapping a
  writer is a data race (two threads touching the same memory at once, with undefined results), not
  a stale snapshot. `get(id)` is safe once the `intern` that produced `id` happens-before it (has
  completed and been made visible to the reading thread) and no further mutation is in flight.

Heavy concurrent interning serialises on the one mutex. See {doc}`/guide/thread_safety`.

::::

::::{tab-item} {{ py_tab }}
:sync: py

The same C++ mutex (a lock that lets one thread in at a time) applies underneath, and `serialize` /
`deserialize` release the GIL. `intern`, `find` and `clear` are safe to call from several threads; `get`, `contains`, `size` and `empty` are
safe only while no thread is interning, clearing or deserializing. `deserialize` **replaces** the
contents when it finishes, so an `intern` from another thread during a load is discarded — do not
intern while a load is running, or repeat the interns after it. See {doc}`/guide/thread_safety`.

::::

:::::

## The registry type

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

`gdt::registry<Key, Tag, Payload>` — non-copyable, non-movable singleton.

Methods:

- `static instance()` — the singleton
- `intern(key, payload)` → `id_type`; `intern(value)` → `id_type` (only when `key_is_payload`);
  both {term}`[[nodiscard]] <nodiscard>`
- `find(key)` → `std::optional<id_type>` (an ID, or empty) — lookup without inserting
- `get(id)` → `const Payload&`; throws `std::out_of_range` for an unknown id
- `contains(id)`, `size()`, `empty()`
- `clear()`; `static reset()`
- `serialize(os)`; `static deserialize(is)` → `registry&`
- `id_type` (`uint32_t`), `null_id`, `key_is_payload` — type and constants

::::

::::{tab-item} {{ py_tab }}
:sync: py

`Registry` — singleton.

Methods:

- `Registry.instance()` — the singleton
- `intern(value)` → `int`; `intern(key, payload)` → `int`
- `find(key)` → `int | None` (an `int`, or `None` when absent) — lookup without inserting
- `get(id)` → payload; `IndexError` for an unknown id
- `contains(id)`, `size()` / `len(r)`, `empty()`
- `clear()`; `Registry.reset()`
- `serialize(path)`; `Registry.deserialize(path)` → `Registry`
- `Registry.null_id` — `2**32 - 1`

::::

:::::