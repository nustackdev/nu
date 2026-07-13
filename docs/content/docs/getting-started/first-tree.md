---
title: Your first tree
---

Store a counter, add 42, print the result.

```python
import nu


class Counter(nu.Shape):
    value: nu.v.IntRef


tree = nu.With(
    nu.v.presets.memory_navigator(),
    body=nu.v.Transaction(
        Counter.value.store(0)
        >> Counter.value.store(Counter.value + 42),
    )
    >> nu.v.Snapshot(nu.print(Counter.value)),
)


nu.run(tree)
```

Save as `counter.py`, run `python counter.py`, and it prints `42`.

## What happened

**Shape.** `Counter` declares one location: `value`, an int, on the virtuals Fabric. Nothing exists in storage yet, the class only names the topology.

**Nothing runs at import.** `Counter.value.store(0)` doesn't store anything. It builds a Command, a tree node describing a write. `Counter.value + 42` doesn't add. It builds a Query. Every expression you compose is a tree, not a value.

**`>>` composes.** Sequential. Left runs, then right. The `+` in `Counter.value + 42` reads the current value at eval time, adds 42, and hands the result to the second `store`.

**Transaction wraps writes.** `nu.v.Transaction(...)` opens one atomic write on the virtuals Fabric around its body. Snapshot does the same for reads. Both are Spans, transparent wrappers that add a lifecycle around whatever they hold.

**`nu.With` binds a Fabric.** `nu.v.presets.memory_navigator()` opens an in-memory virtuals Navigator and hands it to `body`. Every Ref inside resolves through it.

**`nu.run` evaluates.** It walks the tree against a fresh Context, resolves every Ref, executes every Command. The `print` Command lands the value on stdout.

## Swap the world

Change one line and the same tree runs against RocksDB on disk:

```python
tree = nu.With(
    nu.v.presets.rocksdb_navigator_inmemory("./counter.db"),
    body=...,  # same as above
)
```

Same Shape, same composition. Only the Fabric changed. That is the whole model.
