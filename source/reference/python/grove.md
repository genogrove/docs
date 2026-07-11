# Grove

The universal `Grove` (`grove<genomic_coordinate, json>`) and the point-key
groves `NumericGrove` / `KmerGrove`, together with the key and result wrappers
they return. See the {doc}`User Guide </guide/grove/grove>` for the conceptual
model, insertion modes, and the graph overlay.

## Groves

```{eval-rst}
.. autoclass:: pygenogrove.Grove
.. autoclass:: pygenogrove.NumericGrove
.. autoclass:: pygenogrove.KmerGrove
```

## Keys

```{eval-rst}
.. autoclass:: pygenogrove.Key
.. autoclass:: pygenogrove.NumericKey
.. autoclass:: pygenogrove.KmerKey
```

## Query and flanking results

```{eval-rst}
.. autoclass:: pygenogrove.QueryResult
.. autoclass:: pygenogrove.NumericQueryResult
.. autoclass:: pygenogrove.KmerQueryResult
.. autoclass:: pygenogrove.FlankingResult
.. autoclass:: pygenogrove.NumericFlankingResult
.. autoclass:: pygenogrove.KmerFlankingResult
```