# StringRegistry

`StringRegistry` exposes genogrove's `registry<std::string>` — a process-wide
**string-interning singleton** that maps distinct strings to small, stable integer
ids (deduplicated). Handy for interning chromosome names, sources, gene ids, etc.

```python
import pygenogrove as pg

r = pg.StringRegistry.instance()
a = r.intern("chr1")     # 0
b = r.intern("chr1")     # 0  (deduplicated -> same id)
r.get(a)                 # "chr1"
r.find("chr2")           # None (lookup without inserting)
r.serialize("names.gg")
```

## Surface

- `StringRegistry.instance()` — the singleton.
- `intern(value: str) -> int` — idempotent (same value → same id).
- `find(value: str) -> int | None` — lookup without inserting.
- `get(id: int) -> str` — raises `IndexError` on an invalid id.
- `contains(id)`, `size()` / `len(r)`, `empty()`, `clear()`, `StringRegistry.reset()`.
- `StringRegistry.null_id` (= `2**32 − 1`).
- `serialize(path)` / `StringRegistry.deserialize(path)` — binary; `deserialize`
  loads into the singleton, **replacing** current data.

:::{note}
It is a **singleton** — one global pool per process. Use `reset()` / `clear()` to
wipe it (e.g. between runs or tests).

The underlying binding is generic, but only the `std::string` instantiation is
exposed today. Tagged pools and the key→payload metadata form are not yet bound.
:::