# Structure

The `genogrove::structure` namespace contains core data structures for genomic data storage and querying.

## Tag Types

### sorted_t

```{eval-rst}
.. doxygenstruct:: genogrove::structure::sorted_t
   :members:
   :undoc-members:
```

### bulk_t

```{eval-rst}
.. doxygenstruct:: genogrove::structure::bulk_t
   :members:
   :undoc-members:
```

## string_hash

```{eval-rst}
.. doxygenstruct:: genogrove::structure::string_hash
   :members:
   :undoc-members:
```

## grove

Both `grove` and `node` are **non-copyable, move-only** types (Rule of Five). Copy construction
and copy assignment are deleted because these classes manage owned raw pointers—a shallow copy
would cause double-free. Move construction and move assignment are provided so groves can be
returned from functions (e.g., `grove::deserialize()`) and stored in containers.

```{eval-rst}
.. doxygenclass:: genogrove::structure::grove
   :members:
   :undoc-members:
```

## node

`node` is **non-copyable, move-only** (same rationale as `grove`). The move constructor and move
assignment operator transfer ownership of child pointers and leave the source node empty.

```{eval-rst}
.. doxygenclass:: genogrove::structure::node
   :members:
   :undoc-members:
```

## graph_overlay

```{eval-rst}
.. doxygenclass:: genogrove::structure::graph_overlay
   :members:
   :undoc-members:
```
