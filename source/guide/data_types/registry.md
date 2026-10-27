# Registry

A **registry** interns values: every distinct key gets one stable 4-byte ID, and interning the same
key again returns the existing ID. Use it to collapse the thousands of repeats of the same string in
a dataset — chromosome names, transcript or gene IDs, sample identifiers — into one small integer you
store as a grove payload, and look the string up again when you need it.

## Getting the registry

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

`gdt::registry<Key, Tag = void, Payload = Key>` is a **process-wide singleton per template
instantiation**: `registry<std::string>::instance()` always returns the same object.

```cpp
#include <genogrove/data_type/registry.hpp>

namespace gdt = genogrove::data_type;

auto& reg = gdt::registry<std::string>::instance();
```

- `Key` — the identity that is deduplicated; must satisfy `registry_value` (see below)
- `Tag` — a phantom type that separates pools of the same `Key` type (see [Separate pools](#separate-pools))
- `Payload` — what is stored against each ID; defaults to the key itself (see [Richer payloads](#richer-payloads))

::::

::::{tab-item} {{ py_tab }}
:sync: py

`Registry` is a **process-wide singleton** mapping a string key to a JSON payload
(the C++ `registry<std::string, void, json_value>`):

```python
import pygenogrove as pg

r = pg.Registry.instance()
```

There is one pool per process. Multiple independent registries are not exposed in Python.

::::

:::::

## Interning and looking up

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

```cpp
auto id1 = reg.intern("chr1");          // 0 — new
auto id2 = reg.intern("chr1");          // 0 — already present, same ID
auto id3 = reg.intern("chr2");          // 1

reg.find("chr3");                       // std::optional<id_type>, empty — not interned, nothing added
reg.find("chr1");                       // optional{0}
const std::string& name = reg.get(id1); // "chr1"

reg.size();                             // 2
reg.empty();                            // false
reg.contains(id1);                      // true
reg.contains(999);                      // false
```

IDs are `registry::id_type` (`uint32_t`), handed out in insertion order from 0; `registry::null_id`
(`UINT32_MAX`) is reserved and never returned. A pool can hold up to `null_id` entries; `intern`
throws `std::runtime_error` on the entry after that. `get(id)` with an unknown ID throws
`std::out_of_range`.

Store the ID in the grove instead of the string:

```cpp
#include <genogrove/structure/grove/grove.hpp>
#include <genogrove/data_type/interval.hpp>

namespace gst = genogrove::structure;

gst::grove<gdt::interval, gdt::registry<std::string>::id_type> g(100);
g.insert_data("chr1", gdt::interval{100, 200}, reg.intern("SampleA_liver"));
```

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
```

IDs are handed out in insertion order from 0; `Registry.null_id` (`2**32 - 1`) is reserved. `get(id)`
with an unknown id raises `IndexError`.

Store the id in a grove payload instead of the string:

```python
g = pg.Grove(100)
g.insert("chr1", pg.GenomicCoordinate("+", 100, 200), {"sample": r.intern("SampleA_liver")})
```

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
struct gene_info { std::string gene_name; std::string gene_biotype; };
using gene_reg = gdt::registry<std::string, void, gene_info>;

auto id1 = gene_reg::instance().intern("ENSG001", {"FOO", "protein_coding"});
auto id2 = gene_reg::instance().intern("ENSG001", {"placeholder", ""});   // id1 == id2; payload kept from the first call
const gene_info& info = gene_reg::instance().get(id1);                    // {"FOO", "protein_coding"}
```

The one-argument `intern(value)` exists only when `Key == Payload` (`registry::key_is_payload`).
This pattern avoids giving `gene_info` an `operator==` / `std::hash` that only looks at the ID, which
would leak a partial notion of equality to everyone else holding a `gene_info`.

::::

::::{tab-item} {{ py_tab }}
:sync: py

The payload is any JSON-serializable value; the two-argument `intern(key, payload)` stores it:

```python
gid = r.intern("ENSG001", {"name": "BRCA2", "biotype": "protein_coding"})
r.intern("ENSG001", {"name": "placeholder"})      # same id; payload kept from the first call
r.get(gid)                                          # {'name': 'BRCA2', 'biotype': 'protein_coding'}
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
type that costs nothing at runtime and appears nowhere in storage or serialization.

```cpp
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

Not available: Python has the one process-wide `Registry`. Keep unrelated pools apart by prefixing
keys (`"tx:ENST00000001"`, `"src:HAVANA"`) or by keeping the ids in separate payload fields.

::::

:::::

## Requirements on the key type

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

`Key` must satisfy the `registry_value` concept: `std::equality_comparable` and hashable through
`std::hash<Key>`. `std::string` and the integer types qualify, as do `genomic_coordinate`, `numeric`
and `kmer` (each ships a `std::hash` specialisation), so `registry<gdt::genomic_coordinate>` compiles
as-is. `interval` has no `std::hash` and cannot be a registry key without one. A custom type needs
both `operator==` and a `std::hash` specialisation.

::::

::::{tab-item} {{ py_tab }}
:sync: py

Keys are strings. Any `str` works; other key types are not exposed.

::::

:::::

## Clearing

Clearing removes every entry and **invalidates every ID handed out so far** — payloads stored in a
grove that refer to them become meaningless. Do it between runs or tests, not while IDs are in use.

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

```cpp
reg.clear();                              // on the instance
gdt::registry<std::string>::reset();      // the same, as a static call
```

::::

::::{tab-item} {{ py_tab }}
:sync: py

```python
r.clear()                                 # on the instance
pg.Registry.reset()                       # the same, as a static call
```

::::

:::::

## Persistence

A registry is saved and loaded separately from any grove. When grove payloads hold registry IDs,
write the registry **first** and read it back **first**, so the IDs resolve (see
{doc}`/guide/serialization`).

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

```cpp
#include <fstream>

std::ofstream out("names.bin", std::ios::binary);
reg.serialize(out);

std::ifstream in("names.bin", std::ios::binary);
auto& restored = gdt::registry<std::string>::deserialize(in);   // replaces the singleton's contents
```

- Wire format: with `Key == Payload`, a `uint64_t` count then each payload; otherwise `(key, payload)`
  pairs in ID order. Each value is written through `gdt::serializer<Payload>` (and
  `gdt::serializer<Key>` when they differ), so a custom payload such as the `gene_info` above must be
  trivially copyable, or `serialization_traits` must be specialised for it — see
  {doc}`/guide/serialization`.
- `deserialize` offers a **strong exception guarantee**: it builds into temporaries and commits only
  after the whole stream has been read, so a truncated or corrupt stream leaves the singleton exactly
  as it was. It throws `std::runtime_error` for a count beyond `id_type` capacity
  (`"...entry count exceeds id_type capacity"`) and for a duplicate key (`"...duplicate key"`).

::::

::::{tab-item} {{ py_tab }}
:sync: py

```python
r.serialize("names.gg")                    # keys and JSON payloads
r2 = pg.Registry.deserialize("names.gg")   # loads into the singleton, replacing its contents
```

`deserialize` raises `RuntimeError` on a truncated or corrupt file and leaves the singleton as it was.
Both calls release the GIL.

::::

:::::

## Thread safety

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

One internal `std::mutex` per singleton.

- **Locked**: `intern()`, `find()`, `clear()`, `serialize()`, and the final commit of `deserialize()`
  (its I/O and parsing run unlocked, so a long load does not block `intern` / `find`). Because the
  commit **replaces** the contents, an `intern()` that ran while a `deserialize()` was in flight is
  discarded and its ID may now refer to a different loaded value — do not intern concurrently with a
  load, or repeat the interns after it.
- **Unlocked**: `get(id)`, `contains(id)`, `size()`, `empty()`. These are safe only while no writer
  (`intern`, `clear`, `reset`, `deserialize`) runs concurrently; an unlocked read overlapping a
  writer is a data race, not a stale snapshot. `get(id)` is safe once the `intern` that produced `id`
  happens-before it and no further mutation is in flight.

Heavy concurrent interning serialises on the one mutex. See {doc}`/guide/thread_safety`.

::::

::::{tab-item} {{ py_tab }}
:sync: py

The same C++ mutex applies underneath, and `serialize` / `deserialize` release the GIL. `intern`,
`find` and `clear` are safe to call from several threads; `get`, `contains`, `size` and `empty` are
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
  both `[[nodiscard]]`
- `find(key)` → `std::optional<id_type>` — lookup without inserting
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
- `find(key)` → `int | None` — lookup without inserting
- `get(id)` → payload; `IndexError` for an unknown id
- `contains(id)`, `size()` / `len(r)`, `empty()`
- `clear()`; `Registry.reset()`
- `serialize(path)`; `Registry.deserialize(path)` → `Registry`
- `Registry.null_id` — `2**32 - 1`

::::

:::::