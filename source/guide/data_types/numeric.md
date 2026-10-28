# Numeric

A **point** {term}`key type` holding one 32-bit signed integer. It has no range: two values
"{term}`overlap`" only when they are **equal**, so a {term}`grove` keyed by `numeric` is a sorted
dictionary of integers — `intersect` is an exact lookup, {term}`flanking` gives the nearest values on
either side. Use it for ids, ranks or positions you look up exactly.

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

The comments show what each line evaluates to; the lines compute the value without printing it, so
wrap one in `std::cout << ... << '\n';` to see it. The constructor is `explicit`: write
`gdt::numeric{100}`, a bare `100` is not converted on its own. A default-constructed `numeric`
(`gdt::numeric{}`) holds `INT_MIN`, the smallest 32-bit value, not zero. Always pass a value.
`INT_MIN` is also a valid key: `numeric{}` is equal to `numeric{INT_MIN}` and overlaps it, so do not
use it to mean "missing".

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

The comments show what each line evaluates to; in an interactive Python session each line prints its
result. Signature (for reference, not to paste):

```python
Numeric(value: int)      # -2**31 <= value <= 2**31 - 1
```

`Numeric` holds a 32-bit signed integer: a value outside `-2**31 .. 2**31 - 1` raises a `TypeError`
{term}`exception` (not `ValueError`), from both the constructor and `set_value`. `Numeric()` with no
argument holds `-2**31`, not zero. That value is also a valid key: `Numeric()` is equal to
`Numeric(-2**31)`, so do not use it to mean "missing". Always pass a value.

::::

:::::

## The numeric type

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

`gdt::numeric` — one `int` (a 32-bit signed integer).

Methods:

- `get_value()`, `set_value(v)` — `set_value` only on a value you have not inserted yet (see
  {doc}`index`)
- `static overlaps(a, b)` — `a == b`
- `static aggregate(a, b)` — the larger value
- `to_string()` — the number as text
- `serialize(os)`, `static deserialize(is)` — binary persistence ({term}`serialization`)
- `<`, `>`, `==` — integer ordering
- `std::hash<numeric>` — specialised (see {doc}`index`), so it works in unordered containers and as a
  {term}`registry` key

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
#include <genogrove/structure/grove/grove.hpp>
#include <genogrove/data_type/numeric.hpp>
#include <string>

namespace gdt = genogrove::data_type;
namespace gst = genogrove::structure;

gst::grove<gdt::numeric, std::string> ids(100);               // numeric keys, std::string payloads
ids.insert_data("samples", gdt::numeric{42}, "sample-42");    // "samples" is the index

auto hit = ids.intersect(gdt::numeric{42}, "samples");        // exact lookup: 1 key
hit.get_keys().front()->get_data();                           // "sample-42"

auto nb = ids.flanking(gdt::numeric{40}, "samples");          // nearest below / above 40
nb.get_successor()->get_value().get_value();                  // 42 (key -> numeric -> int)
```

`"samples"` is the {term}`index`: in a numeric grove it is simply the name of one tree, not a
chromosome. `100` is the tree {term}`order`, `std::string` the {term}`payload` type. `get_keys()`
holds {term}`key handles <key handle>` ({term}`pointers <pointer>`), hence the `->`.

::::

::::{tab-item} {{ py_tab }}
:sync: py

```python
import pygenogrove as pg

ids = pg.NumericGrove(100)
ids.insert("samples", pg.Numeric(42), {"label": "sample-42"})    # "samples" is the index

list(ids.intersect(pg.Numeric(42), "samples"))[0].data   # {'label': 'sample-42'}
ids.flanking(pg.Numeric(40), "samples").successor.value  # Numeric(42)
```

`"samples"` is the {term}`index`: in a numeric grove it is simply the name of one tree, not a
chromosome. `100` is the tree {term}`order`, the dict the {term}`payload`. `intersect` returns a
{term}`QueryResult`, hence the `list(...)`; `.data` on a {term}`Key <key handle>` is the payload.

`NumericGrove` has the same surface as `Grove` (payloads, graph edges, serialization) with `Numeric`
keys — see {doc}`/guide/grove/index`.

::::

:::::