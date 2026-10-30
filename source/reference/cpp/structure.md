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

Both class templates constrain their first parameter with the `key_type_base` concept
(`template <gdt::key_type_base key_type, typename data_type = void, typename edge_data_type = void>
class grove;` and `template <gdt::key_type_base key_type, typename data_type = void> class node;`),
matching `grove_view`. A key type missing one of the concept's six operations fails at the user's
`grove<my_type>` instantiation with a diagnostic naming `key_type_base` and the missing operation.

Both `grove` and `node` are **non-copyable, move-only** types (Rule of Five). Copy construction
and copy assignment are deleted because these classes manage owned raw pointers—a shallow copy
would cause double-free. Move construction and move assignment are provided so groves can be
returned from functions (e.g., `grove::deserialize()`) and stored in containers.

```{eval-rst}
.. doxygenclass:: genogrove::structure::grove
   :members:
   :undoc-members:
```

## grove_view

`grove_view` is a **read-only, partial reader** over a serialized format 0.4 `.gg`: it loads only
the blocks a query walks instead of deserializing the whole file, complementing the eager `grove`
(see {doc}`the partial reading guide </guide/serialization/partial_reading>`). It is **non-copyable and non-movable**
(it owns the file handle and a zlib state) — obtain one by value from the static `open()` factory,
which relies on guaranteed copy elision.

```{eval-rst}
.. doxygenclass:: genogrove::structure::grove_view
   :members:
   :undoc-members:
```

## node

`node` is **non-copyable, move-only** (same rationale as `grove`). The move constructor and move
assignment operator transfer ownership of child pointers and leave the source node empty.

The navigation getters come in const and non-const pairs, like `get_keys()` / `get_children()`:
`node* get_parent()` / `const node* get_parent() const`, `node* get_next()` /
`const node* get_next() const`, and `node* get_child(int)` / `const node* get_child(int) const`.
Code that stored a const overload's result in a `node*` must switch to `const node*` or navigate
from a non-const node; no runtime behavior changed.

`get_subtree_max()` returns the largest key in the node's subtree (a borrowed pointer into the
grove's key storage, `nullptr` for an empty subtree). It is the routing separator for unsorted
insertion; the separator keys themselves are subtree bounding boxes used for query pruning, not
routing keys. The cache is maintained by the in-memory insert/remove paths and rebuilt on
`grove::deserialize()`; `refresh_subtree_max()` recomputes one node in O(1) from its children and
`refresh_subtree_max_recursive()` refreshes a whole subtree post-order. The paged `grove_view`
leaves it null, since nothing there routes by maximum.

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
