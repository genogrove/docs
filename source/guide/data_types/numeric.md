# Numeric

A **point** key holding one 32-bit signed integer. It has no range: two values "overlap" only when
they are **equal**, so a grove keyed by `numeric` is a sorted dictionary of integers — `intersect`
is an exact lookup, `flanking` gives the nearest values on either side. Use it for ids, ranks or
positions you look up exactly.

## Building a value

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

```cpp
#include <genogrove/data_type/numeric.hpp>

namespace gdt = genogrove::data_type;

gdt::numeric n1{100};
gdt::numeric n2{200};

n1 < n2;                                          // true — ordinary integer ordering
gdt::numeric::overlaps(n1, gdt::numeric{100});    // true  — equal values
gdt::numeric::overlaps(n1, n2);                   // false
gdt::numeric::aggregate(n1, n2);                  // numeric{200} — the larger of the two
n1.to_string();                                   // "100"
```

The constructor is `explicit`. A default-constructed `numeric` holds `INT_MIN` — the identity for
`aggregate`, not zero — so always pass a value.

::::

::::{tab-item} {{ py_tab }}
:sync: py

```python
import pygenogrove as pg

n1 = pg.Numeric(100)
n2 = pg.Numeric(200)

n1 < n2                                      # True — ordinary integer ordering
pg.Numeric.overlaps(n1, pg.Numeric(100))     # True  — equal values
pg.Numeric.overlaps(n1, n2)                  # False
n1.value, str(n1)                            # 100, "100"
```

```python
Numeric(value: int)      # -2**31 <= value <= 2**31 - 1
```

`Numeric` wraps a C++ 32-bit `int`: a value outside `-2**31 .. 2**31 - 1` raises `TypeError` (not
`ValueError`), from both the constructor and `set_value`. `Numeric()` with no argument is the
sentinel `INT_MIN`, not zero — always pass a value.

::::

:::::

## The numeric type

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

`gdt::numeric` — one `int`.

Methods:

- `get_value()`, `set_value(v)` — `set_value` only on a value you have not inserted yet (see
  {doc}`index`)
- `static overlaps(a, b)` — `a == b`
- `static aggregate(a, b)` — the larger value
- `to_string()` — the number as text
- `serialize(os)`, `static deserialize(is)` — binary persistence
- `<`, `>`, `==` — integer ordering
- `std::hash<numeric>` — specialised, so it works in unordered containers and as a `registry` key

::::

::::{tab-item} {{ py_tab }}
:sync: py

`Numeric` — attribute `value` (read-only).

Methods:

- `set_value(v)` — only on a value you have not inserted yet (see {doc}`index`); `TypeError` when
  out of the 32-bit range
- `Numeric.overlaps(a, b)` — static; `a == b`
- `<`, `<=`, `>`, `>=`, `==`, `hash()`, `str()`, `repr()` — integer ordering

::::

:::::

## In a grove

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

```cpp
gst::grove<gdt::numeric, std::string> ids(100);
ids.insert_data("samples", gdt::numeric{42}, "sample-42");

auto hit = ids.intersect(gdt::numeric{42}, "samples");        // exact lookup: 1 key
auto nb  = ids.flanking(gdt::numeric{40}, "samples");         // nearest below / above 40
```

::::

::::{tab-item} {{ py_tab }}
:sync: py

```python
ids = pg.NumericGrove(100)
ids.insert("samples", pg.Numeric(42), {"label": "sample-42"})

list(ids.intersect(pg.Numeric(42), "samples"))[0].data   # {'label': 'sample-42'}
ids.flanking(pg.Numeric(40), "samples").successor.value  # Numeric(42)
```

`NumericGrove` has the same surface as `Grove` (payloads, graph edges, serialization) with `Numeric`
keys — see {doc}`/guide/grove/index`.

::::

:::::