# File readers and I/O

Single-pass readers for the common genomic formats, random-access FASTA, the
format detector, and the record/flag types they yield. See the
{doc}`User Guide </guide/io>` for the iteration contract and grove-loading
workflows.

## Readers

```{eval-rst}
.. autoclass:: pygenogrove.BedReader
.. autoclass:: pygenogrove.GffReader
.. autoclass:: pygenogrove.BamReader
.. autoclass:: pygenogrove.VcfReader
.. autoclass:: pygenogrove.FastaReader
.. autoclass:: pygenogrove.FastaIndex
```

## Record types

```{eval-rst}
.. autoclass:: pygenogrove.SamEntry
.. autoclass:: pygenogrove.FastaEntry
.. autoclass:: pygenogrove.VcfEntry
.. autoclass:: pygenogrove.SampleGenotype
```

## Alignment flags

```{eval-rst}
.. autoclass:: pygenogrove.SamFlags
.. autoclass:: pygenogrove.AlignmentFlags
```

## Format detection

```{eval-rst}
.. autoclass:: pygenogrove.FiletypeDetector
.. autoclass:: pygenogrove.Filetype
.. autoclass:: pygenogrove.CompressionType
```