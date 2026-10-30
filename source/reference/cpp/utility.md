# Utility

The `genogrove::utility` namespace contains helpers shared across the library.

## Little-endian I/O

The functions in `genogrove/utility/le_io.hpp` write and read fixed-width little-endian values, so a serialized `.gg` file reads the same on every platform. Use them in a custom `serialization_traits` specialization.

### wire_scalar

```{eval-rst}
.. doxygenconcept:: genogrove::utility::wire_scalar
```

### write_le

```{eval-rst}
.. doxygenfunction:: genogrove::utility::write_le
```

### read_le

```{eval-rst}
.. doxygenfunction:: genogrove::utility::read_le
```

### write_size

```{eval-rst}
.. doxygenfunction:: genogrove::utility::write_size
```

### read_size

```{eval-rst}
.. doxygenfunction:: genogrove::utility::read_size
```
