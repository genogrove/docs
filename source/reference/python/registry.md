# Registry

`Registry` exposes genogrove's `registry<std::string, void, json_value>` — a
process-wide singleton mapping a string key to any JSON-serializable payload. See
the {doc}`User Guide </guide/data_types/registry>` for usage and the two `intern`
forms.

```{eval-rst}
.. autoclass:: pygenogrove.Registry
```