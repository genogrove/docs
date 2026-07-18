# Thread Safety

Genogrove does very little internal synchronization. The core `grove` and its embedded
`graph_overlay` hold **no locks** — treat them as *not thread-safe* for concurrent mutation. A small
number of components (the `registry`, and in Python `FastaIndex` construction) are synchronized. This
page states exactly what is and isn't safe, so you can add your own coordination where you need it.

:::{warning}
There is no per-index or per-chromosome locking. A grove does **not** support "one chromosome per
thread" concurrent insertion — different chromosomes still share the same internal key storage and
root-node map, so concurrent writes race regardless of which index they target.
:::

:::::{tab-set}

::::{tab-item} {{ cpp_tab }}
:sync: cpp

### The core grove is not thread-safe

`grove<key_type, data_type, edge_data_type>` and its embedded `graph_overlay` contain no mutexes.
Their state — the per-index B+ trees reachable from the root-node map, the shared key storage, and
the graph adjacency map — is plain unsynchronized memory.

Consequently, **any mutation concurrent with any other access to the same grove is a data race**
(undefined behavior). Mutating operations include `insert_data`, `insert`, `remove_key`, `compact`,
`add_edge`, `remove_edge(s)`, `link_if`, `add_external_key`, and `deserialize`. This holds even when
two threads target different chromosomes: they still touch the shared root-node map and key storage.

### What concurrent access *is* safe

- **Concurrent reads of a grove that no thread mutates.** Once a grove is fully built and will not be
  modified again, any number of threads may query it simultaneously — `intersect`, `flanking`, and
  `get_neighbors` only read grove state and build their own local result. (This is the standard C++
  guarantee for concurrent `const` access, not a grove feature; note that `intersect` happens to lack
  a `const` qualifier but performs no mutation.)
- **Independent groves in different threads.** Separate grove instances share nothing except the
  process-wide `registry` (below), so operating on them in parallel is safe.

### Coordinating concurrent mutation

If you need to mutate a grove from multiple threads, add your own synchronization. A
`std::shared_mutex` around the grove matches its read/write pattern well:

```cpp
std::shared_mutex mtx;
genogrove::structure::grove<gdt::interval, std::string> g(64);

// Writer
{
    std::unique_lock lock(mtx);
    g.insert_data("chr1", {100, 200}, "feat", gst::sorted);
}

// Reader
{
    std::shared_lock lock(mtx);
    auto hits = g.intersect(gdt::interval{100, 200}, "chr1");
}
```

Alternatively, build one grove per thread and combine the results downstream (there is no in-place
grove-merge API — serialize each, or query the set of groves).

### The registry is the one synchronized component

`genogrove::data_type::registry<Key, Tag, Payload>` is a process-wide singleton guarded by a single
internal `std::mutex` (one global lock — not sharded, not per-index):

- **Locked:** `intern()`, `find()`, `clear()`, `serialize()`, and the commit step of `deserialize()`.
  `deserialize()` builds into local temporaries and only takes the lock for a brief move-assign, so it
  does not block concurrent `intern`/`find` during I/O.
- **Unlocked fast paths:** `get(id)`, `contains(id)`, `size()`, `empty()`. `get(id)` is safe alongside
  concurrent `intern()` **only if** the `id` came from an `intern()` that happens-before the `get()`.

Because it is a single global mutex, heavy concurrent interning serializes on it.

### `grove_view` — one per thread

The partial reader `grove_view` is **not thread-safe**: a query pages blocks into a per-view cache and
advances a single `ifstream` plus zlib state. Use one `grove_view` per thread — open the same `.gg`
multiple times if several threads need to query it.

### Serialization

`serialize()` / `deserialize()` take no locks and touch the whole structure. Treat them as exclusive
operations: no other access to the grove being (de)serialized while they run.

### Verifying your own concurrency

Build genogrove with `-DENABLE_THREAD_SANITIZER=ON` and run your multithreaded code under
ThreadSanitizer to catch races in how you share groves.

::::

::::{tab-item} {{ py_tab }}
:sync: py

In pygenogrove, concurrency is governed by CPython's **GIL** plus a couple of native locks. The GIL
means pure-Python threads won't *corrupt* a `Grove`, but it also serializes any method that holds it,
so multithreading buys parallelism only where the binding releases the GIL.

### GIL released — overlaps other threads' work

These methods drop the GIL around their native work, so a long-running call on one thread does not
freeze others:

- `Grove.serialize(path)`
- `Grove.deserialize(path)` (static)
- `Grove.to_sif(path)`
- `insert_bulk(...)` — released around the native build loop

### GIL held — serialized

These keep the GIL for the duration, so concurrent calls run one at a time:

- `intersect`, `get_neighbors`, `flanking`
- every predicate-callback method — `link_if` / `link_with`, `get_neighbors_if`, `remove_edges_if` —
  because the native code re-enters Python to call your predicate

### A `Grove` is still not internally synchronized

Sharing a single `Grove` across threads gives you no parallelism for the GIL-holding methods above,
and the underlying C++ grove has no locks. For real parallel throughput, use one `Grove` per worker
(or per process) rather than contending on a shared instance.

### `GroveView` — one per thread

`GroveView` (and `NumericGroveView` / `KmerGroveView` / `BedGroveView` / `GffGroveView`) is **not
thread-safe** — a query mutates the view's block cache and holds the GIL. Use one view per thread.

### `FastaIndex` construction is serialized

htslib's `fai_load()` is not thread-safe, so `FastaIndex` construction takes a process-wide lock
(with the GIL released around the build, so unrelated threads aren't frozen). Reads through separate
`FastaIndex` handles remain concurrent.

::::

:::::