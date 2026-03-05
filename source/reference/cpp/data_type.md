# Data Types

The `genogrove::data_type` namespace contains genomic data type definitions and utilities.

## key_type_base Concept

The `key_type_base` concept defines the requirements for custom key types used with the grove:

- `a < b`, `a > b`, `a == b` — Comparison operators
- `T::overlaps(a, b)` — Static overlap detection returning `bool`
- `T::aggregate(a, b)` — Static pairwise aggregation returning `T`
- `a.to_string()` — String representation

All built-in key types (`interval`, `genomic_coordinate`, `numeric`, `kmer`) satisfy this concept.

## interval

```{eval-rst}
.. doxygenclass:: genogrove::data_type::interval
   :members:
   :undoc-members:
```

## genomic_coordinate

```{eval-rst}
.. doxygenclass:: genogrove::data_type::genomic_coordinate
   :members:
   :undoc-members:
```

## key

```{eval-rst}
.. doxygenclass:: genogrove::data_type::key
   :members:
   :undoc-members:
```

## query_result

```{eval-rst}
.. doxygenclass:: genogrove::data_type::query_result
   :members:
   :undoc-members:
```

## numeric

```{eval-rst}
.. doxygenclass:: genogrove::data_type::numeric
   :members:
   :undoc-members:
```

## kmer

```{eval-rst}
.. doxygenclass:: genogrove::data_type::kmer
   :members:
   :undoc-members:
```

## data_registry

```{eval-rst}
.. doxygenclass:: genogrove::data_type::data_registry
   :members:
   :undoc-members:
```

## index

```{eval-rst}
.. doxygenclass:: genogrove::data_type::index
   :members:
   :undoc-members:
```

## index_registry

```{eval-rst}
.. doxygenclass:: genogrove::data_type::index_registry
   :members:
   :undoc-members:
```

## Serialization Utilities

### serialization_traits

```{eval-rst}
.. doxygenstruct:: genogrove::data_type::serialization_traits
   :members:
   :undoc-members:
```

### serializer

```{eval-rst}
.. doxygenstruct:: genogrove::data_type::serializer
   :members:
   :undoc-members:
```
