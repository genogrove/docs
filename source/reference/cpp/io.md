# I/O

The `genogrove::io` namespace contains file readers and parsers for genomic file formats.

## Readers

### filetype_detector

```{eval-rst}
.. doxygenclass:: genogrove::io::filetype_detector
   :members:
   :undoc-members:
```

### bed_reader

```{eval-rst}
.. doxygenclass:: genogrove::io::bed_reader
   :members:
   :undoc-members:
```

### gff_reader

```{eval-rst}
.. doxygenclass:: genogrove::io::gff_reader
   :members:
   :undoc-members:
```

### bam_reader

```{eval-rst}
.. doxygenclass:: genogrove::io::bam_reader
   :members:
   :undoc-members:
```


## Entry Types

### bed_entry

```{eval-rst}
.. doxygenclass:: genogrove::io::bed_entry
   :members:
   :undoc-members:
```

### gff_entry

```{eval-rst}
.. doxygenstruct:: genogrove::io::gff_entry
   :members:
   :undoc-members:
```

### sam_entry

```{eval-rst}
.. doxygenstruct:: genogrove::io::sam_entry
   :members:
   :undoc-members:
```

## Reader Options

### bed_reader_options

```{eval-rst}
.. doxygenstruct:: genogrove::io::bed_reader_options
   :members:
   :undoc-members:
```

### gff_reader_options

```{eval-rst}
.. doxygenstruct:: genogrove::io::gff_reader_options
   :members:
   :undoc-members:
```

### bam_reader_options

```{eval-rst}
.. doxygenstruct:: genogrove::io::bam_reader_options
   :members:
   :undoc-members:
```

## BED Support Types

### rgb_color

```{eval-rst}
.. doxygenstruct:: genogrove::io::rgb_color
   :members:
   :undoc-members:
```

### thick_info

```{eval-rst}
.. doxygenstruct:: genogrove::io::thick_info
   :members:
   :undoc-members:
```

### block_info

```{eval-rst}
.. doxygenstruct:: genogrove::io::block_info
   :members:
   :undoc-members:
```

## BAM/SAM Types

### sam_flags

```{eval-rst}
.. doxygenstruct:: genogrove::io::sam_flags
   :members:
   :undoc-members:
```

### alignment_flags

```{eval-rst}
.. doxygenclass:: genogrove::io::alignment_flags
   :members:
   :undoc-members:
```

### cigar_element

```{eval-rst}
.. doxygenstruct:: genogrove::io::cigar_element
   :members:
   :undoc-members:
```

### mate_info

```{eval-rst}
.. doxygenstruct:: genogrove::io::mate_info
   :members:
   :undoc-members:
```

### sam_tag

```{eval-rst}
.. doxygenstruct:: genogrove::io::sam_tag
   :members:
   :undoc-members:
```

## Enums

### filetype

```{eval-rst}
.. doxygenenum:: genogrove::io::filetype
```

### compression_type

```{eval-rst}
.. doxygenenum:: genogrove::io::compression_type
```

### gff_format

```{eval-rst}
.. doxygenenum:: genogrove::io::gff_format
```

### cigar_op

```{eval-rst}
.. doxygenenum:: genogrove::io::cigar_op
```
