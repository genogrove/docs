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

## Grove views (partial random-access readers)

Read-only, partial readers over a serialized `.gg` — page in only the blocks a
query touches. See the {doc}`Serialization guide </guide/serialization>`.

```{eval-rst}
.. autoclass:: pygenogrove.GroveView
.. autoclass:: pygenogrove.NumericGroveView
.. autoclass:: pygenogrove.KmerGroveView
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