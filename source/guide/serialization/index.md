# Serialization

A {term}`grove` can be written to disk and loaded back later ({term}`serialization`), so you parse
and insert your data once instead of on every run. For large datasets this is much faster than
rebuilding the grove from the source files. The file is a {term}`zlib`-compressed binary
{term}`stream`; by project convention it carries the `.gg` extension (a {term}`.gg file`), and the
{term}`genogrove` {term}`CLI` writes the same stream behind a small {doc}`file header <format>`.

This page covers saving and loading a whole grove. The subpages cover the two more specialised
topics:

- {doc}`partial_reading` — querying a `.gg` on disk without loading all of it (`grove_view` /
  `GroveView`, a {term}`view`)
- {doc}`format` — how the stream is laid out, {term}`format versions <format version>` and
  compatibility, the `.gg` file header written by the CLI, and {term}`SIF` export for visualisation

Some C++ snippets are complete programs and some are fragments to put in `main()`.
{doc}`/guide/installation` shows how to compile and link them against genogrove, and
{doc}`/guide/quickstart` builds the first grove they save.

## Saving and loading

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

`serialize` writes the grove to an output stream; the static {term}`deserialize` reads one back
and returns a new grove.

```cpp
#include <genogrove/structure/grove/grove.hpp>
#include <genogrove/data_type/interval.hpp>
#include <fstream>

namespace gdt = genogrove::data_type;
namespace gst = genogrove::structure;

int main() {
    gst::grove<gdt::interval, std::string> my_grove(100);
    my_grove.insert_data("chr1", gdt::interval{100, 200}, "gene1");
    my_grove.insert_data("chr1", gdt::interval{300, 400}, "gene2");

    // Save to disk
    {
        std::ofstream out("grove.gg", std::ios::binary);
        my_grove.serialize(out);
    }

    // Load from disk
    {
        std::ifstream in("grove.gg", std::ios::binary);
        auto loaded = gst::grove<gdt::interval, std::string>::deserialize(in);
        // loaded is a fully functional grove with all data restored
    }

    return 0;
}
```

Always open streams with `std::ios::binary` to avoid platform-specific newline translation.

The file extension does not matter to the library — `grove.bin` would be read just the same. `.gg`
is the project convention. Note that the CLI's own `.gg` files carry a 12-byte header in front of
the grove stream, so `isec -i` does not accept a file written by `serialize` directly — see
{doc}`format` and the {doc}`CLI reference </cli>`. Python's `serialize` writes no such header
either.

Assign the result of `deserialize` to a variable, as the example does. You cannot copy a grove, and
you do not need to. The {term}`template` arguments must match those the grove was written with: the
key type, the payload type and the edge type, in the same order. The stream records the key kind and whether payload and edge metadata are present, and `deserialize` throws `std::runtime_error` if those differ (see [type check](format.md#type-check-on-read)). It does not record the payload or edge type itself.

A grove can be saved through a read-only reference. `serialize()` is **{term}`const`-qualified**
(as are `grove_to_sif()` and `node::serialize_block()`), so code that only has a read-only
reference to a grove (`const grove&`) can still save it:

```cpp
void persist(const gst::grove<gdt::interval, std::string>& g, std::ostream& os) {
    g.serialize(os);   // OK — serialize() is const
}
```

**Reading a Python `.gg` from C++.** A file written by {term}`pygenogrove`'s universal `Grove`
stores each payload and each edge's metadata as JSON text. To read it, use
`grove<genomic_coordinate, std::string, std::string>`: the key type, then the payload type (JSON
text), then the edge type (JSON text). If the file has **no edges at all**, you can use the shorter
`grove<genomic_coordinate, std::string>`. With edges, you must use the three-type form, because
every edge writes metadata (JSON `null` for an unlabelled one) and the short form cannot skip it. The
typed `BedGrove` / `GffGrove` files are read with `grove<genomic_coordinate, bed_entry>` /
`grove<genomic_coordinate, gff_entry>`.

::::

::::{tab-item} {{ py_tab }}
:sync: py

`serialize(path)` writes the grove to a file; the static `Grove.deserialize(path)` reads one back
and returns a new grove. Both take a file path rather than a stream, and both
{term}`release the GIL <GIL>`.

```python
import pygenogrove as pg

g = pg.Grove(100)
g.insert("chr1", pg.GenomicCoordinate("+", 100, 200), "gene1")
g.insert("chr1", pg.GenomicCoordinate("+", 300, 400), "gene2")

g.serialize("grove.gg")
reloaded = pg.Grove.deserialize("grove.gg")     # a fully functional grove with all data restored
```

The universal `Grove` takes a `GenomicCoordinate` (a strand plus start and end) as key where the C++ example
uses a plain `interval`; the intervals and payloads are the same.

```python
serialize(path: str) -> None
Grove.deserialize(path: str) -> Grove
```

Load a file with the grove class that wrote it: a `BedGrove` file with `BedGrove.deserialize`, a
`NumericGrove` file with `NumericGrove.deserialize`, and so on (the classes are introduced in
{doc}`/guide/grove/index`). The file records the key kind and whether it holds payloads and edge metadata, so a mismatch raises `RuntimeError`. It does not record which class wrote it, so two classes with the same key kind and payload presence are not told apart.

**Reading a Python `.gg` from C++.** A universal `Grove` stores each {term}`payload` and each
edge's {term}`metadata <edge metadata>` as JSON text, so a C++ program can read its file. The
C++ tab shows which C++ grove type to use for each Python grove class.

::::

:::::

## What is saved

Everything the grove holds is written: every {term}`index` (chromosome) with its {term}`keys <key>`
and payloads, and the {term}`graph overlay` — every {term}`edge` with its metadata, including the
relative order of each key's incoming edges — so neighbours can be followed after a reload exactly
as before. The {term}`B+ tree` structure itself is stored too, so loading does not rebuild or
re-balance anything.

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

All built-in {term}`key types <key type>` (`interval`, `genomic_coordinate`, `numeric`, `kmer`) and
the common data types are serialized automatically:

- **Numbers and strings** — `int`, `double`, `uint32_t` and `std::string` are saved without extra
  code
- **`gio::bed_entry`** (with its nested `gio::block_info`) and **`gio::gff_entry`** — member
  `serialize` / `deserialize` provided, so a `grove<gdt::interval, gio::bed_entry>` can be persisted
  directly (the {doc}`CLI </cli>`'s `idx` indexes are groves of this kind with a `std::string` edge
  type — see {doc}`format`). `gio::rgb_color` and `gio::thick_info` are trivially copyable and
  serialize automatically.

Any other key or data type needs a small amount of code — see [Custom key types](#custom-key-types)
and [Custom data types](#custom-data-types) below.

::::

::::{tab-item} {{ py_tab }}
:sync: py

Nothing needs to be declared. Payloads of the universal `Grove` (and `NumericGrove` / `KmerGrove`)
are JSON values and are stored as JSON text; `BedGrove` / `GffGrove` store their `BedEntry` /
`GffEntry` records in the same binary form the C++ library uses. Edge metadata is stored the same
way as payloads.

::::

:::::

## Saving a registry with a grove

When a {doc}`registry </guide/data_types/registry>` holds shared metadata that the grove refers to
by ID (sample names, for example), save the registry as well, and restore it **before** you use the
IDs stored in the grove.

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

Both objects can share one stream. Write the registry first, then the grove, and read them back in
the same order. `instance()` returns the program-wide registry (a {term}`singleton`); `intern`
stores a name once and returns its integer ID ({term}`interning`), and `get` turns the ID back into
the name:

```cpp
#include <genogrove/structure/grove/grove.hpp>
#include <genogrove/data_type/interval.hpp>
#include <genogrove/data_type/registry.hpp>
#include <fstream>
#include <iostream>

namespace gdt = genogrove::data_type;
namespace gst = genogrove::structure;

int main() {
    auto& reg = gdt::registry<std::string>::instance();
    gst::grove<gdt::interval, uint32_t> my_grove(100);

    // Intern shared metadata, store IDs in the grove
    auto id1 = reg.intern("SampleA_liver");
    auto id2 = reg.intern("SampleB_brain");
    my_grove.insert_data("chr1", gdt::interval{100, 200}, id1);
    my_grove.insert_data("chr1", gdt::interval{150, 250}, id2);

    // Save: registry first, then grove
    {
        std::ofstream out("data.gg", std::ios::binary);
        reg.serialize(out);
        my_grove.serialize(out);
    }

    // Load: same order. reg.clear() empties the registry, as in a new program run
    reg.clear();
    {
        std::ifstream in("data.gg", std::ios::binary);
        auto& restored = gdt::registry<std::string>::deserialize(in);
        auto loaded = gst::grove<gdt::interval, uint32_t>::deserialize(in);

        // Registry IDs in the grove still resolve correctly
        auto results = loaded.intersect(gdt::interval{100, 200}, "chr1");
        for (auto* key : results.get_keys()) {
            const auto& name = restored.get(key->get_data());
            std::cout << name << "\n";        // "SampleA_liver" and "SampleB_brain" (both overlap)
        }
    }

    return 0;
}
```

This works because `grove::deserialize` reads exactly its own bytes and leaves whatever follows in
the stream untouched — see [Streams and errors](#streams-and-errors).

::::

::::{tab-item} {{ py_tab }}
:sync: py

The Python API takes a path per object, so the registry and the grove go into two files. Write
both, and load the registry before resolving IDs from the grove. `intern` stores a name once and
returns its integer ID ({term}`interning`); `get` turns the ID back into the name, and `key.data`
is the key's payload (see {doc}`/guide/data_types/key`):

```python
import pygenogrove as pg

reg = pg.Registry.instance()
g = pg.Grove(100)

id1 = reg.intern("SampleA_liver")
id2 = reg.intern("SampleB_brain")
g.insert("chr1", pg.GenomicCoordinate("+", 100, 200), {"sample": id1})
g.insert("chr1", pg.GenomicCoordinate("+", 150, 250), {"sample": id2})

reg.serialize("names.reg")
g.serialize("grove.gg")

# Load: registry first, then the grove. reg.clear() empties the registry, as in a new program run
reg.clear()
reg = pg.Registry.deserialize("names.reg")
g = pg.Grove.deserialize("grove.gg")
for key in g.intersect(pg.GenomicCoordinate("*", 100, 200), "chr1"):
    print(reg.get(key.data["sample"]))   # "SampleA_liver" and "SampleB_brain" (both overlap)
```

C++ stores the value itself; the Python example stores a dict that labels the value (a bare JSON number or string works as well).

`Registry.deserialize` loads into the {term}`singleton` (the one registry the whole program
shares), **replacing** its contents; see {doc}`/guide/data_types/registry` for its guarantees.

**One registry, not many.** C++ can have many registries, one for each combination of key type and
payload type, and each has its own file. pygenogrove has exactly one: `Registry`, with string keys
and JSON payloads. There is one registry file per Python process, whatever it is used for. A
`Registry` file is **not** the same as the registry file of the C++ tab, because the C++ registry in
that tab has no payload column. A C++ program reads a Python `Registry` file with
`registry<std::string, void, std::string>` (string keys, string payloads) and parses the JSON text
itself.

::::

:::::

## Custom key types

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

A {doc}`custom key type </guide/grove/custom_key_types>` must provide a `serialize` member method
and a static `deserialize` factory:

```cpp
struct CustomInterval {
    size_t start;
    size_t end;

    void serialize(std::ostream& os) const {
        os.write(reinterpret_cast<const char*>(&start), sizeof(start));
        os.write(reinterpret_cast<const char*>(&end), sizeof(end));
    }

    [[nodiscard]] static CustomInterval deserialize(std::istream& is) {
        CustomInterval ci;
        is.read(reinterpret_cast<char*>(&ci.start), sizeof(ci.start));
        is.read(reinterpret_cast<char*>(&ci.end), sizeof(ci.end));
        if (!is) throw std::runtime_error("Failed to deserialize CustomInterval");
        return ci;
    }

    // ... other key_type_base requirements (operator<, overlap, aggregate, etc.)
};
```

`[[nodiscard]]` ({term}`nodiscard`) makes the compiler warn if a caller ignores the returned value;
the `reinterpret_cast<const char*>` lets `write` and `read` see a number as its raw bytes.

::::

::::{tab-item} {{ py_tab }}
:sync: py

Already covered: each pygenogrove grove class has a fixed key type (`GenomicCoordinate`, `Numeric`
or `Kmer`), and all three serialize automatically (see {doc}`/guide/data_types/index`). Defining
your own key type is a C++ feature.

::::

:::::

## Custom data types

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

For a custom payload type there are two options.

**Option 1: member methods.** Add `serialize` and a static `deserialize` to your type, as for a key
type. `gdt::serializer<T>` writes and reads the built-in types for you:

```cpp
struct Annotation {
    std::string name;
    double score;

    void serialize(std::ostream& os) const {
        genogrove::data_type::serializer<std::string>::write(os, name);
        os.write(reinterpret_cast<const char*>(&score), sizeof(score));
    }

    [[nodiscard]] static Annotation deserialize(std::istream& is) {
        auto name = genogrove::data_type::serializer<std::string>::read(is);
        double score;
        is.read(reinterpret_cast<char*>(&score), sizeof(score));
        if (!is) throw std::runtime_error("Failed to deserialize Annotation");
        return {std::move(name), score};
    }
};
```

**Option 2: specialise `serialization_traits`.** For a third-party type you cannot modify, provide
the two functions outside the type instead:

```cpp
#include <genogrove/data_type/serialization_traits.hpp>

template<>
struct genogrove::data_type::serialization_traits<ThirdPartyType> {
    static void serialize(std::ostream& os, const ThirdPartyType& value) {
        // write fields to os
    }

    static ThirdPartyType deserialize(std::istream& is) {
        // read fields from is and return constructed object
    }
};
```

::::

::::{tab-item} {{ py_tab }}
:sync: py

Already covered (see {doc}`/guide/data_types/key`): payloads are JSON values, so any dict, list, string, number, boolean or `None`
— nested as deeply as you like — is serialized as JSON text without further work. Whether a value
is representable as JSON is checked at insert time, not at serialization time: an arbitrary Python
object raises `TypeError`, a `NaN` or infinite float `ValueError`.

::::

:::::

## Streams and errors

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

**Non-seekable sources.** `grove::deserialize()` reads the stream front to back and stops exactly
where the grove ends. It never jumps back in the source, and it leaves the bytes after the grove
unread. It therefore works on **non-{term}`seekable` sources**: pipes, sockets and custom stream
buffers, which you can read only once, in order. A registry followed by a grove, several groves
back-to-back, or an end marker of your own can all share one stream.

```{note}
Random-access *partial* reading via {doc}`grove_view <partial_reading>` still needs a seekable
source — it seeks to individual block offsets — which is why `grove_view::open` takes a file path
rather than an arbitrary stream.
```

**Errors.** Every `deserialize` (`grove::deserialize`, `node::deserialize_block`,
`registry::deserialize`, `serialization_traits<std::string>::deserialize`) throws
`std::runtime_error` (an {term}`exception`) on a corrupt or truncated stream, and on a stream of a
different format than the build reads (bad {term}`magic`; see {doc}`format` for which build reads
which format). `node::deserialize_block` additionally validates the B+ tree invariants — the size
rules every {term}`node` must satisfy (`num_keys < order`, `num_children <= order`). All
`deserialize` methods are `[[nodiscard]]`, so accidentally discarding the result is a compiler
warning.

A registry load that fails leaves the registry untouched. `registry::deserialize` gives a
**{term}`strong exception guarantee`**: if the stream throws or is truncated, the singleton is left
exactly as it was. It also rejects an entry count that exceeds the `id_type` capacity (more entries
than the ID's integer type can number) and streams containing duplicate keys — see
{doc}`/guide/data_types/registry`.

::::

::::{tab-item} {{ py_tab }}
:sync: py

**Files only.** `serialize` / `deserialize` take a path and open the file themselves; there is no
stream {term}`overload`. Where the C++ tab puts several objects in one file, a Python program uses
one file per object.

**Errors.** `Grove.deserialize` raises `RuntimeError` (an {term}`exception`) if the file cannot be
opened, is not a format 0.4 grove, or is corrupt or truncated. `serialize` raises `RuntimeError` if
the file cannot be opened or written. `Registry.deserialize` raises `RuntimeError` on a truncated or
corrupt file and leaves the registry as it was.

::::

:::::

```{toctree}
:maxdepth: 1
:hidden:

partial_reading
format
```