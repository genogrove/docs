# CLI

The genogrove command-line interface provides tools for indexing and querying genomic interval files.

## Commands

### idx (Index)

Builds an index from a BED or GFF/GTF file and writes it to a zlib-compressed `.gg` index file — a
serialized grove holding the records as payloads. The index can later be searched directly with
`isec -i`, avoiding a re-parse of the source file.

The input file type is detected automatically and determines the grove type written:

- BED → `grove<interval, bed_entry>`, stored with `.gg` payload_type `0x01` (BED)
- GFF3/GTF → `grove<interval, gff_entry>`, stored with `.gg` payload_type `0x02` (GFF)
- anything else → error `"unsupported input format"`

**Usage:**

```bash
genogrove idx [OPTIONS] <inputfile>
```

**Options:**

- `-o, --outputfile <file>`: Output index file (default: `<inputfile>.gg`, written next to the input)
- `-k, --order <int>`: B+ tree order (default: 3, minimum: 3)
- `-s, --sorted`: Assert the input intervals are coordinate-sorted (enables the faster sorted-append path)
- `-l, --links <file>`: Attach directed graph edges from a name-keyed TSV (BED input only — see [Links](#links-attaching-graph-edges) below)
- `-t, --timed`: Print the indexing time

**Examples:**

```bash
# Build target.bed.gg next to the input file
genogrove idx target.bed

# Write the index to a specific path
genogrove idx target.bed -o /data/target.gg

# Pre-sorted input, with timing
genogrove idx -s -t sorted.bed

# Index a GFF/GTF file
genogrove idx annotation.gff3 -o annotation.gg

# Attach graph edges from a links TSV (BED input only)
genogrove idx features.bed -l links.tsv -o features.gg
```

```{note}
The `.gg` header records a `payload_type` byte that distinguishes index types (`0x01` BED,
`0x02` GFF). `isec` uses this byte to instantiate the correct grove type. See the
serialization / file-format guide for the full header layout.
```

```{note}
`idx` builds the grove fully in memory before opening the output file, so a parse error
mid-insert (or a malformed links file) aborts before any existing `.gg` at the output path
is touched — it can never leave a truncated index behind.
```

#### Links: attaching graph edges

`idx -l/--links FILE` attaches directed edges to the grove's `graph_overlay` from a name-keyed
TSV. The edges are part of grove serialization, so a later `isec -i` against the resulting `.gg`
sees them with no extra work.

**Links file format** — a 2-column TSV:

- Comment lines (starting with `#`) and blank lines are skipped.
- Each row `nameA<TAB>nameB` adds a directed edge `nameA → nameB`.
- Names are matched against BED column 4 (the `name` field).
- A row that is not exactly two non-empty tab-separated columns is an error naming the line number.

**Constraints:**

- BED input only — GFF/GTF links are a future follow-up.
- Names must be unique within the BED file; a duplicate column-4 name aborts indexing.
- Every linked name must resolve to a BED record; an unresolved name aborts, naming the missing name.
- Repeated rows are de-duplicated, because `graph_overlay::add_edge` does not deduplicate (see the
  graph edges guide).
- Per-edge metadata is not yet supported (2-column TSV only).

The grove and its edges are built fully in memory before the output `.gg` is opened, so a malformed
links file or unresolved name aborts before any existing `.gg` at the output path is touched.

**Example** — a BED6 with named features:

```text
chr1    100    200    geneA    0    +
chr1    300    400    geneB    0    +
chr1    500    600    geneC    0    +
```

and a links TSV (`links.tsv`):

```text
# regulatory edges
geneA    geneB
geneB    geneC
```

build an index whose graph edges are visible through the library's graph accessors and to `isec`:

```bash
genogrove idx features.bed -l links.tsv -o features.gg

# The edges geneA → geneB and geneB → geneC travel with the .gg
genogrove isec -q regions.bed -i features.gg
```

### isec (Intersect)

Finds overlapping intervals between a query file and a target. The target can be built on the fly
from a BED or GFF/GTF file (`-t`) or loaded from a prebuilt `.gg` index (`-i`).

`isec` dispatches on type: with `-i <prebuilt.gg>` the `.gg` header's `payload_type` byte tells it
which grove type to instantiate; with `-t <target>` the file-type detector picks the path.

**Usage:**

```bash
genogrove isec -q <queryfile> (-t <targetfile> | -i <indexfile>) [OPTIONS]
```

**Options:**

- `-q, --queryfile <file>`: Query BED file (required)
- `-t, --targetfile <file>`: Target BED file to build the grove from (one of `-t` / `-i` required)
- `-i, --indexfile <file>`: Prebuilt `.gg` index to search against (one of `-t` / `-i` required)
- `-o, --outputfile <file>`: Output destination (default: stdout)
- `-k, --order <int>`: B+ tree order used when building from `-t` (default: 3, minimum: 3)

Either `-t` or `-i` must be supplied — at least one is required. When both are given, `-i` takes
precedence and `-t` is ignored. `-k` only affects the grove built from `-t`; an index loaded via
`-i` keeps the order it was created with.

```{note}
Cross-type queries (for example a BED query against a GFF index) are deliberately rejected in this
release — the query, target, and index types must match.
```

**Examples:**

```bash
# Find overlaps, building the target grove from a BED file
genogrove isec -q regions.bed -t genes.bed

# Search a prebuilt index instead of a BED file
genogrove isec -q regions.bed -i genes.gg

# Write results to a file
genogrove isec -q regions.bed -t genes.bed -o overlaps.bed

# Use a higher tree order when building from a target
genogrove isec -q regions.bed -t genes.bed -k 5

# Compressed inputs are handled transparently
genogrove isec -q regions.bed.gz -t genes.bed.gz
```

### Index-then-search workflow

Build an index once, then reuse it across many queries:

```bash
# 1. Build the index from a target BED file
#    Writes genes.gg and prints "Index written to genes.gg" on success.
genogrove idx genes.bed -o genes.gg

# 2. Search the prebuilt index — no need to re-parse genes.bed
#    Writes overlapping BED records to stdout (use -o to redirect to a file).
genogrove isec -q regions.bed -i genes.gg
```

## Supported Formats

Currently supported:

- BED format (`.bed`, `.bed.gz`) — for query and target input, and for `idx` links (`-l`)
- GFF/GTF format (`.gff3`, `.gtf`, gzip-compressed variants) — for query and target input
- `.gg` index files (produced by `idx`) — for the `isec -i` search target

```{note}
Query, target, and index types must match — cross-type intersection (e.g. a BED query against a
GFF index) is not supported in this release. The `.gg` `payload_type` byte (`0x01` BED, `0x02` GFF)
records which type an index holds.
```

Planned support:

- GFF/GTF links for `idx -l` (currently BED-only)
- Per-edge link metadata
- VCF format
