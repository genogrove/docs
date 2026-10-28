# Glossary

Short definitions of the terms the guide uses. Each entry links to the page that explains the
concept in full. The first group is genogrove's own vocabulary; the second group covers the
programming terms the C++ and Python tabs rely on.

## genogrove terms

```{glossary}
grove
  The central data structure: one B+ tree per {term}`index` (chromosome), holding
  {term}`keys <key>` that can be searched by overlap, plus an optional {term}`graph overlay`.
  In C++ `gst::grove<key_type, data_type, edge_data_type>`; in Python `Grove`, `BedGrove`,
  `GffGrove`, `NumericGrove` or `KmerGrove`. See {doc}`grove/index`.

index
  Used in three senses, which the guide tries to keep apart:

  1. **index (chromosome)** — the name that selects one tree inside a grove. It is the first
     argument of every insert and the second of every query (`"chr1"`). A tree is created the
     first time an insert names it. See {doc}`grove/index`.
  2. **index file** — the `.gg` file written by the CLI's `idx` command, holding a serialized grove
     that `isec -i` queries. See {doc}`/cli`.
  3. **B+ tree index** — the sorted structure itself, in the database sense. The guide says
     "tree" for this.

key
  One stored item: a {term}`key type` value (where it is) plus an optional {term}`payload` (what it
  is). Inserts and queries hand back **key handles**: a pointer in C++, a `Key` object in Python.
  Handles stay valid until {term}`compact` is called. See {doc}`data_types/key`.

key type
  The value a grove sorts and searches on. Four are built in: `interval` and
  `genomic_coordinate` for regions, `numeric` and `kmer` for exact matches. Every grove is built on
  exactly one. See {doc}`data_types/index`.

payload
  The data attached to a key — a name, a file record such as `BedEntry`, or (Python) any JSON
  value. The tree never looks at it. Also called the key's *data*. In C++ it is the `data_type`
  template argument; `void` means "keys without data". See {doc}`data_types/key`.

0-based closed
  genogrove's coordinate convention: positions count from 0 and **both** ends are included, so
  `[100, 200]` covers bases 100 through 200 and has length `end - start + 1`. BED, BAM and VCF
  use 0-based half-open `[start, end)` and convert as `[start, end - 1]`; GFF/GTF use 1-based
  closed and convert as `[start - 1, end - 1]`. See {doc}`io/index`.

strand
  Which DNA strand a feature lies on: `'+'`, `'-'`, or `'.'` for a feature with no strand.
  `'*'` is a **wildcard** used in queries and matches any strand; `'.'` is a real value that
  matches only `'.'`. Two `genomic_coordinate` values overlap only when their ranges share a base
  **and** their strands are compatible. See {doc}`data_types/interval_coordinate`.

overlap
  Two regions overlap when they share at least one base (for stranded coordinates, with compatible
  strands). `intersect` returns every stored key that overlaps the query. For `numeric` and
  `kmer` keys "overlap" means equality. See {doc}`grove/querying`.

flanking
  The nearest keys on either side of a query that do **not** overlap it: the *predecessor* (just
  before) and the *successor* (just after). Either may be absent. See {doc}`grove/querying`.

order
  The B+ tree's branching factor: the maximum number of children per node (and `order - 1` keys).
  It is the only constructor argument of a grove; 100 is a good default and 3 the minimum. See
  {doc}`grove/index` and {doc}`performance`.

sorted insert
  An insert that promises the new key is greater than every key already in that index, letting
  the grove append without searching. The promise is not checked; breaking it silently corrupts
  the tree. See {doc}`grove/inserting`.

bulk insert
  Inserting a whole sorted batch for one index at once. On an empty index the tree is built
  bottom-up, which is 10–20× faster than single inserts. See {doc}`grove/inserting`.

compact
  Rebuilding a grove's key storage after removals so it holds only live keys. It invalidates
  **every** key handle obtained before. See {doc}`grove/removing`.

graph overlay
  Optional directed edges between the keys of a grove, which may cross chromosomes and carry their
  own metadata. The tree answers "what is here?", the graph "what is this connected to?". Saved
  and restored with the grove. See {doc}`graph/index`.

edge
  One directed link from a *source* key to a *target* key in the graph overlay. Following edges
  forwards gives a key's *neighbours*, backwards its *in-neighbours*. See {doc}`graph/navigating`.

edge metadata
  Data attached to an edge (a label, a weight). In C++ its type is the grove's third template
  argument, `void` for plain edges; in Python `Grove` edges carry any JSON value while
  `BedGrove` / `GffGrove` edges carry none. See {doc}`graph/building`.

external key
  A key that lives only in the graph overlay: it takes part in edges but is never returned by
  `intersect` or `flanking`. Used for things that have no position, such as a transcription
  factor or a sample. See {doc}`graph/building`.

seed
  In the CLI's `isec --hops`, an interval that overlaps the query and from which the edge walk
  starts. See {doc}`/cli`.

registry
  A process-wide table that turns a repeated value (a sample name, a gene symbol) into a small
  integer ID, so keys can store the ID instead of the string. Called *interning*. C++ has one
  registry per template instantiation; Python has a single `Registry`. See {doc}`data_types/registry`.

interning
  Storing a value once in a {term}`registry` and referring to it by its ID everywhere else.

k-mer
  A DNA sequence of fixed length *k*, here up to 32 bases packed two bits per base. The `kmer`
  key type makes a grove a k-mer set or counter. See {doc}`data_types/kmer`.

serialization
  Writing a grove to a file and reading it back, so the data is parsed and inserted only once.
  The file is a compressed binary and by convention has the `.gg` extension. See
  {doc}`serialization/index`.

.gg file
  A serialized grove. A file written by `serialize` is a bare grove stream; one written by the
  CLI's `idx` has a 12-byte header in front of the same stream. See {doc}`serialization/format`.

format version
  The version of the `.gg` layout, currently 0.3. A genogrove build reads exactly one format;
  older files must be regenerated. See {doc}`serialization/format`.

view
  A read-only reader (`grove_view` / `GroveView`) that opens a `.gg` and loads only the parts a
  query touches, instead of the whole file. The opposite is the *eager* grove, which loads
  everything with `deserialize`. See {doc}`serialization/partial_reading`.

eager
  Loading or building the whole grove in memory, as `deserialize` does — in contrast to a
  {term}`view`.

SIF
  Simple Interaction Format, a tab-separated text format read by Cytoscape. A grove can be
  exported to it for visualisation. See {doc}`serialization/format`.
```

## Programming terms

```{glossary}
B+ tree
  The sorted, balanced tree a grove is built on. Values sit in the bottom row of **leaf** nodes,
  linked left to right; the **internal** nodes above only route a search. Looking up a region
  walks one path from the root to a leaf, so the cost grows with the logarithm of the number of
  keys, not with the number itself.

node
  One block of a B+ tree holding up to `order - 1` keys. A *leaf* holds the stored keys; an
  *internal node* holds separators and child pointers.

handle
  A value that refers to something the grove owns without copying it: a raw pointer in C++, a
  `Key` object in Python. See {term}`key`.

pointer
  (C++) The address of an object, written with `*`. `auto* k = grove.insert_data(...)` gives a
  pointer to the stored key; `k->get_data()` reaches through it. A **null pointer** (`nullptr`)
  points at nothing; functions that may find nothing return one, so check before dereferencing.

template
  (C++) A class or function with type parameters in angle brackets, filled in at compile time:
  `grove<interval, std::string>` is a grove of intervals with string payloads. Python has no
  equivalent; pygenogrove instead ships one class per combination (`Grove`, `BedGrove`, …).

const
  (C++) A promise not to modify. A `const` method can be called on a read-only object; a
  `const grove&` parameter accepts a grove without copying it or allowing changes.

overload
  Several functions with the same name and different parameters; the compiler or interpreter picks
  by the arguments. `intersect(query)` and `intersect(query, index)` are two overloads.

predicate
  A function that takes a value and returns true or false, passed to another function to filter
  with. In Python usually a `lambda`: `lambda m: m["weight"] > 5`. The `_if` methods and the
  three-argument `flanking` take one.

lambda
  An unnamed function written inline. Python: `lambda cand, q: cand.strand == q.strand`;
  C++: `[](const auto& m) { return m == "activates"; }`.

iterator / iterable
  Something a `for` loop can walk. A `QueryResult` is iterable but not a list: loop over it or
  wrap it in `list(...)`; it has no `[i]` indexing.

stream
  (C++) An object bytes are read from or written to: `std::ifstream` / `std::ofstream` for files.
  Open them with `std::ios::binary` for `.gg` files. The Python API takes file paths instead.

seekable
  A source that can jump to an arbitrary byte position, such as a regular file. Pipes and sockets
  are not seekable. A {term}`view` needs a seekable file; eager `deserialize` does not.

zlib
  The compression library (the `gzip` family) used inside `.gg` files. "zlib-compressed" just
  means compressed; the file is not a `.gz` you can `gunzip`.

magic
  The first few bytes of a file that identify its type (`"GROV"` for a CLI `.gg`). A "bad magic"
  error means the file is not what the reader expected.

singleton
  A class with exactly one instance per process, reached through `instance()` rather than created
  with a constructor. The {term}`registry` is one.

exception
  How an error is reported: the operation stops and an error object travels up to the nearest
  handler. C++ throws `std::invalid_argument` (bad argument), `std::out_of_range` (unknown ID),
  `std::runtime_error` (I/O or corrupt data); Python raises `TypeError`, `ValueError`,
  `IndexError`, `RuntimeError` for the same cases.

strong exception guarantee
  If an operation fails, the object is left exactly as it was before the call. `registry::deserialize`
  gives this guarantee.

nodiscard
  (C++) `[[nodiscard]]`, a marker on a function whose return value must be used; ignoring it is a compiler warning.
  Every `deserialize` is marked this way.

GIL
  (Python) The Global Interpreter Lock: only one Python thread runs Python code at a time. A
  pygenogrove call that **releases the GIL** (file I/O, bulk inserts, serialization) lets other
  Python threads run while it works; a call that holds it does not. See {doc}`thread_safety`.

thread-safe
  Safe to call from several threads at once without extra locking. A grove is **not** thread-safe
  for concurrent mutation (concurrent reads of a grove no thread is changing are fine); a view is
  not thread-safe at all, so use one per thread. See {doc}`thread_safety`.

O(log n), O(n)
  Shorthand for how running time grows with the input size *n*. O(log n) barely grows (a tree
  search); O(n) grows in proportion (a scan of everything); O(1) does not grow at all.
```