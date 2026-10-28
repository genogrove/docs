# Glossary

Short definitions of the terms the guide uses. Each entry links to the page that explains the
concept in full. The first group is genogrove's own vocabulary; the second group covers the
programming terms the C++ and Python tabs rely on. Entries are grouped by topic rather than
alphabetically; use your browser's search to jump to a word.

## genogrove terms

```{glossary}
genogrove
pygenogrove
  **genogrove** is the C++ library; **pygenogrove** is its Python package (`pip install
  pygenogrove`, imported as `pg`). Their version numbers are independent, which is why each guide
  tab shows the version it documents. See {doc}`installation`.

CLI
  The `genogrove` command-line program that ships with the C++ library. Its two commands are
  `idx` (build a `.gg` {term}`index file <index>` from a BED or GFF file) and `isec` (intersect a
  query file with a BED file or a prebuilt index). See {doc}`/cli`.

grove
  The central data structure: one {term}`B+ tree` per {term}`index` (chromosome), holding
  {term}`keys <key>` that can be searched by overlap, plus an optional {term}`graph overlay`.
  In C++ it is a {term}`template`, `gst::grove<key_type, data_type, edge_data_type>`; in Python one
  of `Grove`, `BedGrove`, `GffGrove`, `NumericGrove` or `KmerGrove`. See {doc}`grove/index`.

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
key handle
  A **key** is one stored item: a {term}`key type` value (where it is) plus an optional
  {term}`payload` (what it is). Inserts and queries hand back **key handles** — a
  {term}`pointer` in C++, a `Key` object in Python — through which you read the value and the
  payload. Handles to indexed keys stay valid until {term}`compact` is called. See
  {doc}`data_types/key`.

key type
  The value a grove sorts and searches on. Four are built in: `interval` and
  `genomic_coordinate` for regions (`genomic_coordinate` adds a {term}`strand`, and is the one to
  use for BED/GFF features and the only region type in Python), `numeric` and `kmer` for exact
  matches. Every grove is built on exactly one. See {doc}`data_types/index`.

payload
  The data attached to a key — a name, a file record such as `BedEntry` / `GffEntry` (the Python
  classes for one BED or GFF line), or (Python `Grove`) any JSON value. The tree never looks at
  it. Also called the key's *data*. In C++ it is the `data_type` {term}`template` argument;
  `void` means no payload. See {doc}`data_types/key`.

QueryResult
  What `intersect` returns in Python: the matching {term}`key handles <key>`. Loop over it or
  wrap it in `list(...)`; it has `len()` but no `[i]` indexing. The C++ counterpart is
  `query_result` with `get_keys()`. See {doc}`grove/querying`.

0-based closed
  genogrove's coordinate convention: positions count from 0 and **both** ends are included, so
  `[100, 200]` covers bases 100 through 200 and has length `end - start + 1`. The BED, BAM and
  VCF **readers** expose 0-based {term}`half-open` `[start, end)` records (for VCF the reader has already
  turned the file's 1-based `POS` into `start = POS - 1`), which convert as `[start, end - 1]`;
  the GFF/GTF reader keeps the file's 1-based closed coordinates, which convert as
  `[start - 1, end - 1]`. See {doc}`io/index`.

half-open
  The `[start, end)` convention of BED and BAM files and of the BED, BAM and VCF readers: `end` is
  one past the last base, so the length is `end - start`. Converts to the grove's
  {term}`0-based closed` keys as `[start, end - 1]`. See {doc}`io/index`.

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
  The {term}`B+ tree`'s branching factor: the maximum number of children per {term}`node` (and
  `order - 1` keys). It is the only argument when creating a grove (`Grove(100)`); 100 is a good
  default and 3 the minimum. See {doc}`grove/index` and {doc}`performance`.

sorted insert
  An insert that promises the new key is greater than every key already in that index (for
  regions: starts at or after them, by the key type's own ordering), letting the grove append
  without searching. The promise is not checked; breaking it silently corrupts the tree. See
  {doc}`grove/inserting`.

bulk insert
  Inserting a whole sorted batch for one index at once. On an empty index the tree is built
  bottom-up, which is 10–20× faster than single inserts. See {doc}`grove/inserting`.

compact
  Rebuilding a grove's key storage after removals so it holds only live keys. It invalidates
  **every indexed** key handle obtained before; handles to {term}`external keys <external key>`
  stay valid. See {doc}`grove/removing`.

graph overlay
  Optional directed edges between the keys of a grove, which may cross chromosomes and carry their
  own metadata. The tree answers "what is here?", the graph "what is this connected to?". Saved
  and restored with the grove. See {doc}`graph/index`.

edge
  One directed link from a *source* key to a *target* key in the graph overlay. Following edges
  forwards gives a key's *neighbours*, backwards its *in-neighbours*. See {doc}`graph/navigating`.

parallel edge
  A second edge with the same source and target, in the same direction. `add_edge` never merges
  duplicates, so adding the same pair twice stores two edges, each with its own
  {term}`edge metadata`. See {doc}`graph/index`.

edge metadata
  Data attached to an edge (a label, a weight). In C++ its type is the grove's third template
  argument, `void` for plain edges; in Python `Grove` edges carry any JSON value while
  `BedGrove` / `GffGrove` edges carry none. See {doc}`graph/building`.

external key
  A key that lives only in the graph overlay: it takes part in edges but is never returned by
  `intersect` or `flanking`. Used for things that have no position, such as a transcription
  factor or a sample. See {doc}`graph/building`.

hop
seed
  In the {term}`CLI`'s `isec --hops N`, a **seed** is an interval that overlaps the query, and a
  **hop** is one edge followed from it; `--hops 2` reports everything within two edges of a seed.
  See {doc}`/cli`.

registry
  A table, shared by the whole program, that turns a repeated value (a sample name, a gene symbol)
  into a small integer ID, so keys can store the ID instead of the string. Called *interning*.
  C++ has one registry per combination of key and payload type; Python has a single `Registry`
  with string keys and JSON payloads. See {doc}`data_types/registry`.

interning
  Storing a value once in a {term}`registry` and referring to it by its ID everywhere else. See
  {doc}`data_types/registry`.

k-mer
  A DNA sequence of fixed length *k*, here up to 32 bases packed two bits per base. The `kmer`
  key type makes a grove a k-mer set or counter. See {doc}`data_types/kmer`.

serialization
deserialize
  **Serialization** is writing a grove to a file so the data is parsed and inserted only once;
  **deserialize** is the call that reads such a file back into a new grove (`Grove.deserialize(path)`
  in Python, the static `grove::deserialize(stream)` in C++). The file is a compressed binary and
  by convention has the `.gg` extension. See {doc}`serialization/index`.

.gg file
  A serialized grove. A file written by `serialize` is the bare grove bytes; one written by the
  {term}`CLI`'s `idx` has a 12-byte header in front of the same bytes. `deserialize` cannot read
  an `idx` file directly (the header is in the way), and `isec -i` cannot read a `serialize` file
  (it expects the header); a {term}`view` can read either when told where the grove bytes start.
  See {doc}`serialization/format`.

block
  One independently compressed unit of a `.gg` file: one B+ tree {term}`node`, or one chunk of
  {term}`external keys <external key>`. A {term}`view` loads blocks on demand; `blocks_loaded()`
  and `block_count()` count them. See {doc}`serialization/format`.

format version
  The version of the `.gg` layout, currently 0.3. A genogrove build reads exactly one format;
  older files must be regenerated. See {doc}`serialization/format`.

view
  A read-only reader (`grove_view` / `GroveView`) that opens a `.gg` and loads only the parts a
  query touches, instead of the whole file. The opposite is the *eager* grove, which loads
  everything with `deserialize`. See {doc}`serialization/partial_reading`.

eager
  Loading or building the whole grove in memory, as `deserialize` does — in contrast to a
  {term}`view`. See {doc}`serialization/partial_reading`.

SIF
  Simple Interaction Format, a tab-separated text format read by Cytoscape (a network
  visualisation program). A grove can be exported to it to look at its tree and graph. See
  {doc}`serialization/format`.

htslib
  The C library behind samtools and bcftools. genogrove uses it to read BAM/CRAM, VCF/BCF and
  compressed files, so it must be installed before the C++ library is compiled; the Python package
  from `pip` already contains it. See {doc}`installation`.

bgzip
tabix
  `bgzip` compresses a text file in chunks so that it stays {term}`seekable`; `tabix` writes a
  small companion lookup file (`.tbi` or `.csi`) next to a bgzipped, position-sorted BED, GFF or
  VCF file so that one locus can be read without scanning the whole file. See
  {doc}`io/region_access`.
```

## Programming terms

```{glossary}
B+ tree
  The sorted, balanced tree a grove is built on. Values sit in the bottom row of **leaf** nodes,
  linked left to right; the **internal** nodes above only route a search. Finding the first
  candidate for a region walks one path from the root to a leaf, so that step grows with the
  logarithm of the number of keys, not with the number itself; the query then reads along the
  leaves for as long as they still overlap, so a wide query costs in proportion to its hits.

node
leaf
internal node
  One box of a B+ tree, holding up to `order - 1` keys (see {term}`order`). A *leaf* holds the
  stored keys; an *internal node* holds separators and child pointers, the values that steer a
  search downwards.

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

concept
  (C++) A named list of requirements a type must meet to be used as a {term}`template` argument,
  checked when the code is compiled. `key_type_base` is the concept a {term}`key type` must
  satisfy. See {doc}`grove/custom_key_types`.

move-only
  (C++) A type that can be handed over (`std::move`) but not copied: `auto g2 = g;` is a compile
  error for a `grove`. Pass it as `grove&` or `std::move` it; a {term}`view` cannot even be moved.

std::optional
  (C++) A value that may be absent. Test it like a boolean, read it with `*` or `->`, or supply a
  fallback with `value_or(...)`. The file readers use it for optional columns such as the BED name
  or the GFF strand; Python returns `None` in the same places.

trivially copyable
  (C++) A type that can be copied byte for byte: plain numbers, and structs made only of them.
  Such {term}`payloads <payload>` are serialized automatically, provided the type also has a
  default constructor. A `std::string` or smart-pointer member makes a type not trivially
  copyable, so it needs `serialize` / `deserialize` methods or a `serialization_traits`
  specialisation. A raw pointer member passes the check but would be saved as a meaningless
  address, so such types need the custom methods too. See {doc}`serialization/index`.

hash
  A number computed from a value such that equal values give equal numbers, which is what lets a
  value be used as a dictionary or set key. genogrove provides `std::hash` for
  `genomic_coordinate`, `numeric` and `kmer`; a Python `Key` hashes by its coordinate. See
  {doc}`data_types/index`.

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
  handler. C++ throws `std::invalid_argument` (bad argument), `std::out_of_range` (unknown ID)
  and `std::runtime_error` (I/O, corrupt data, a full registry); Python raises `ValueError`,
  `IndexError` and `RuntimeError` for the same three cases, and additionally `TypeError` when
  `None` is passed where a key is required.

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

O(1)
O(log n)
O(n)
  Shorthand for how running time grows with the input size *n*. O(1) does not grow at all (a
  registry ID lookup); O(log n) barely grows (a tree search); O(n) grows in proportion (a scan of
  everything).
```