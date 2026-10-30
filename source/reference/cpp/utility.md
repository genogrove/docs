# Utility

The `genogrove::utility` namespace contains helpers shared across the library.

## Little-endian I/O

You need these functions only to save your own data type to a `.gg` file. They write a number in a fixed byte order (little-endian), so each number reads the same on any computer. Use them in a custom `serialization_traits` specialization; see {doc}`../../guide/serialization/index` for an example and {doc}`../../guide/serialization/format` for the file layout.

- `write_le` and `read_le` write and read one number.
- `write_size` and `read_size` write and read a count or a position. They always use 8 bytes.
- The `write_` function writes and the `read_` function reads the same form.

Use fixed-width types such as `int32_t` and `uint64_t` in your own types. `long`, `unsigned long` and `wchar_t` take the width of the platform, so a file that holds them can read wrongly on another platform.

### wire_scalar

`wire_scalar` is the rule for which types `write_le` and `read_le` accept: integers, enums, `float` and `double`.

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
