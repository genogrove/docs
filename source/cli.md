# CLI

The genogrove command-line interface provides tools for indexing and querying genomic interval files.

## Global options

- `-v, --version`: Print the genogrove version (`genogrove <major>.<minor>.<patch>`) and exit 0.

```bash
genogrove --version
# genogrove 0.25.3
```

**Invalid arguments** — an unrecognized flag, a non-integer value for an integer option (e.g. `-k foo`),
or a missing option argument reports the error on stderr and exits with status 1:

```bash
genogrove idx -k foo input.bed
# error: invalid value 'foo' for --order
# exit status: 1
```

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
- `-l, --links <file>`: Attach directed graph edges from a name-keyed TSV (BED or GFF/GTF input — see [Links](#links-attaching-graph-edges) below)
- `--gff-name-tag <attr>`: For GFF/GTF input with `--links`, the attribute whose value identifies each record for link matching (e.g. `ID`, `gene_id`, `transcript_id`). Required for `--links` on GFF/GTF; ignored for BED input
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

# Attach graph edges from a links TSV (BED input)
genogrove idx features.bed -l links.tsv -o features.gg

# Attach graph edges to a GFF/GTF index, matching on the ID attribute
genogrove idx genes.gff3 -l links.tsv --gff-name-tag ID -o genes.gg
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

**Links file format** — a 2- or 3-column TSV:

- Comment lines (starting with `#`) and blank lines are skipped.
- Each row `nameA<TAB>nameB` adds a directed edge `nameA → nameB`.
- An optional 3rd tab-separated field attaches per-edge metadata to that edge — a raw string
  (`nameA<TAB>nameB<TAB>supports_isoform=ENST00001`), stored verbatim with no quoting or escaping.
- Names are matched against BED column 4 (the `name` field), or — for GFF/GTF input — against the
  attribute named by `--gff-name-tag` (see below).
- A row that is not exactly 2 or 3 tab-separated columns, or that has any empty column (including a
  present-but-empty 3rd), is an error naming the line number.

**Constraints:**

- BED and GFF/GTF input are supported. On GFF/GTF, `--links` **requires** `--gff-name-tag <attr>`
  — there is no canonical name column, so the identifying attribute must be named explicitly.
  Omitting it aborts indexing.
- Names must be unique within the file; a duplicate BED column-4 name (or a duplicate
  `--gff-name-tag` attribute value) aborts indexing. On GFF/GTF, every record must carry the chosen
  attribute — a missing attribute aborts, naming the record.
- Every linked name must resolve to a record; an unresolved name aborts, naming the missing name.
- Exact-duplicate rows are de-duplicated (`graph_overlay::add_edge` does not deduplicate — see the
  graph edges guide). The dedup key includes the metadata, so the same `(source, target)` pair with
  two *different* metadata values yields two parallel edges.

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

**GFF/GTF input** — because GFF/GTF has no name column, name `--gff-name-tag` to select the
identifying attribute. The values of that attribute must be present on every record and unique
across the file:

```bash
# Match links against the GFF3 ID attribute
genogrove idx genes.gff3 -l links.tsv --gff-name-tag ID -o genes.gg

# Match against a GTF gene_id
genogrove idx genes.gtf -l links.tsv --gff-name-tag gene_id -o genes.gg
```

On BED input `--gff-name-tag` is ignored (BED links always match column 4) — it is not an error.

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

- `-q, --queryfile <file>`: Query BED, GFF/GTF, or VCF/BCF file (required). VCF/BCF is query-only — see [VCF/BCF queries](#vcf-bcf-queries)
- `-t, --targetfile <file>`: Target BED or GFF/GTF file to build the grove from (one of `-t` / `-i` required)
- `-i, --indexfile <file>`: Prebuilt `.gg` index to search against (one of `-t` / `-i` required)
- `--in-place`: Query the prebuilt index (`-i`) on disk, reading only the blocks each query touches instead of loading the whole file into memory (requires `-i`)
- `-o, --outputfile <file>`: Output destination (default: stdout)
- `-k, --order <int>`: B+ tree order used when building from `-t` (default: 3, minimum: 3)

Either `-t` or `-i` must be supplied — at least one is required. When both are given, `-i` takes
precedence and `-t` is ignored. `-k` only affects the grove built from `-t`; an index loaded via
`-i` keeps the order it was created with.

#### Cross-type queries

The query file type and the target/index type are **independent** — all four BED/GFF combinations
work. The query type only selects how query records are iterated; the output format follows the
**target/index** payload type (a `.gg` index holds one payload type):

| Query | Target / Index | Output |
|---|---|---|
| BED | BED | BED rows |
| BED | GFF | GFF rows |
| GFF | BED | BED rows |
| GFF | GFF | GFF rows |
| VCF/BCF | BED | BED rows |
| VCF/BCF | GFF | GFF rows |

(VCF/BCF is query-only — see [VCF/BCF queries](#vcf-bcf-queries) below.)

To make cross-type overlaps correct, both readers map to a common **0-based-inclusive** interval
space internally: BED `[start, end)` → `interval(start, end-1)`; GFF/GTF `[start, end]` (1-based) →
`interval(start-1, end-1)`. The printed output coordinates are unchanged — each hit is emitted with
the raw entry coordinates of the target payload.

```{warning}
The internal GFF interval numbering shifted by −1 to share this space, so the `.gg` on-disk format
changed for GFF payloads. **GFF indexes built before v0.25.0 must be regenerated** (`genogrove idx`).
See the {doc}`serialization guide </guide/serialization>` — there is no serialization back-compat.
```

(vcf-bcf-queries)=
#### VCF/BCF queries

VCF and BCF files are accepted as `-q` query input, alongside BED and GFF/GTF. Both `.vcf` and
`.bcf` (binary) are recognized by extension, so BCF queries work without renaming. A VCF/BCF query
can run against any target/index — a BED or GFF `-t` file, or a `-i` index (eager or `--in-place`) —
and the output format follows the **target/index** payload type, exactly as for the other query
types.

VCF/BCF is **query-only**: it is never a target or an index payload, so there is no `.gg` format
change. Passing a VCF/BCF file to `-t` fails with `unsupported target format (only BED, GFF, and GTF
are supported)`.

Each VCF/BCF record maps into the same canonical **0-based-inclusive** interval space as BED:
`interval(POS-1, POS-1 + len(REF) - 1)` — i.e. `end = POS-1 + len(REF)`, then `interval(start,
end-1)`. A SNP (`len(REF) == 1`) becomes a single-base interval; a multi-base REF spans `len(REF)`
bases.

```{warning}
Structural / symbolic variants (`<DEL>`, `<INS>`, breakends) carry their span in `INFO/END`, which
is **not** currently honored. Such records map positionally by `len(REF)` (single-base only when
`len(REF) == 1`), so overlap for them is positional-only.
```

```bash
# VCF query against a BED target — output is BED rows
genogrove isec -q variants.vcf -t genes.bed

# Binary BCF query against a prebuilt GFF index, read in place
genogrove isec -q variants.bcf -i genes.gg --in-place
```

#### In-place querying

By default `isec -i` deserializes the whole `.gg` into memory. `--in-place` instead queries the
index on disk via a partial reader ([`grove_view`](guide/serialization.md#partial-random-access-reading)),
loading only the blocks each query walks. Output is identical to the eager path — it is a
memory/latency trade-off:

- `--in-place` **requires `-i`**. Using it with a `-t` target (built in memory, no on-disk index)
  errors: `--in-place requires a prebuilt index (-i)`.
- It wins for targeted queries and is the only option when the index is larger than RAM. For a
  dense whole-genome query file the (non-evicting) block cache ends up loading most blocks anyway,
  so it is roughly at parity with the eager path there.

```bash
genogrove isec -q query.bed -i index.gg              # eager (default)
genogrove isec -q query.bed -i index.gg --in-place   # partial read
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
- GFF/GTF format (`.gff3`, `.gtf`, gzip-compressed variants) — for query and target input, and for
  `idx` links (`-l` with `--gff-name-tag`)
- VCF/BCF format (`.vcf`, `.bcf`) — for `isec` query input only (`-q`); see
  [VCF/BCF queries](#vcf-bcf-queries)
- `.gg` index files (produced by `idx`) — for the `isec -i` search target

```{note}
The query type and the target/index type are independent — a BED query may run against a GFF index
and vice versa (see [Cross-type queries](#cross-type-queries)). The `.gg` `payload_type` byte
(`0x01` BED, `0x02` GFF) records which payload an index holds, and the output follows it.
```

Planned support:

- VCF/BCF as a target/index payload type (currently query-only)
- Honoring `INFO/END` for structural / symbolic variants (currently mapped positionally by `len(REF)`)
