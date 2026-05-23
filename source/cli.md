# CLI

The genogrove command-line interface provides tools for indexing and querying genomic interval files.

## Commands

### idx (Index)

Builds an index from a BED file and writes it to a zlib-compressed `.gg` index file — a
serialized grove holding the BED records as `bed_entry` payloads. The index can later be searched
directly with `isec -i`, avoiding a re-parse of the source BED file.

**Usage:**

```bash
genogrove idx [OPTIONS] <inputfile>
```

**Options:**

- `-o, --outputfile <file>`: Output index file (default: `<inputfile>.gg`, written next to the input)
- `-k, --order <int>`: B+ tree order (default: 3, minimum: 3)
- `-s, --sorted`: Assert the input intervals are coordinate-sorted (enables the faster sorted-append path)
- `-t, --timed`: Print the indexing time

**Examples:**

```bash
# Build target.bed.gg next to the input file
genogrove idx target.bed

# Write the index to a specific path
genogrove idx target.bed -o /data/target.gg

# Pre-sorted input, with timing
genogrove idx -s -t sorted.bed
```

```{note}
Only BED input is currently supported (`.bed`, `.bed.gz`). GFF/GTF input is planned.
```

### isec (Intersect)

Finds overlapping intervals between a query file and a target. The target can be built on the fly
from a BED file (`-t`) or loaded from a prebuilt `.gg` index (`-i`).

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

- BED format (`.bed`, `.bed.gz`) — for query and target input
- `.gg` index files (produced by `idx`) — for the `isec -i` search target

Planned support:

- GFF/GTF format
- VCF format