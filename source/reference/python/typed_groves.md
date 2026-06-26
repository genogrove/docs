# Typed groves (BED / GFF)

The schema-typed groves `BedGrove` (`grove<genomic_coordinate, bed_entry>`) and
`GffGrove` (`grove<genomic_coordinate, gff_entry>`), their key and result
wrappers, and the structured record types they carry. See the
{doc}`User Guide </guide/grove/loading_data>` for usage.

## Groves

```{eval-rst}
.. autoclass:: pygenogrove.BedGrove
.. autoclass:: pygenogrove.GffGrove
```

## Keys and results

```{eval-rst}
.. autoclass:: pygenogrove.BedKey
.. autoclass:: pygenogrove.GffKey
.. autoclass:: pygenogrove.BedQueryResult
.. autoclass:: pygenogrove.GffQueryResult
.. autoclass:: pygenogrove.BedFlankingResult
.. autoclass:: pygenogrove.GffFlankingResult
```

## Record types

```{eval-rst}
.. autoclass:: pygenogrove.BedEntry
.. autoclass:: pygenogrove.GffEntry
.. autoclass:: pygenogrove.ThickInfo
.. autoclass:: pygenogrove.RgbColor
.. autoclass:: pygenogrove.BlockInfo
.. autoclass:: pygenogrove.GffFormat
```