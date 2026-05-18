# CLI

The genogrove command-line interface provides tools for indexing and querying genomic interval files.

## Commands

### idx (Index)

```{note}
The `idx` subcommand is **not yet implemented**. The CLI accepts the
arguments but `execute()` currently throws
`std::runtime_error("Error: idx subcommand not yet implemented")`. The
options listed below describe the planned interface — see the [tracking
issue](https://github.com/genogrove/genogrove) for status.
```

Creates an index from an interval file for efficient queries.

**Planned usage:**

```bash
genogrove idx [OPTIONS] <inputfile>
```

**Planned options:**

- `-o, --outputfile <file>`: Specify output file (default: `<inputfile>.gg`)
- `-k, --order <int>`: B+ tree order (default: 3)
- `-s, --sorted`: Flag indicating intervals are pre-sorted
- `-t, --timed`: Display indexing time

### isec (Intersect)

Finds overlapping intervals between query and target files.

**Usage:**

```bash
genogrove isec -q <queryfile> -t <targetfile> [OPTIONS]
```

**Options:**

- `-q, --queryfile <file>`: Query file (required)
- `-t, --targetfile <file>`: Target file (required)
- `-o, --outputfile <file>`: Output destination (default: stdout)
- `-k, --order <int>`: B+ tree order (default: 3)

**Examples:**

```bash
# Find overlaps between files
genogrove isec -q regions.bed -t genes.bed

# Write results to file
genogrove isec -q regions.bed -t genes.bed -o overlaps.bed

# Use higher tree order for large datasets
genogrove isec -q regions.bed -t genes.bed -k 5

# Handle compressed files
genogrove isec -q regions.bed.gz -t genes.bed.gz
```

## Supported Formats

Currently supported:

- BED format (`.bed`, `.bed.gz`)

Planned support:

- GFF/GTF format
- VCF format