# Everybase Benchmarks

Benchmarking suite for the everybase data layer (virtuals + eb_virtuals + everybase.shape) and term tree execution.

## Structure

```
benchmarks/
├── utils.py                    # Shared: counters, timed_run, reporting
│
├── layers/                     # Layer benchmarks -- isolate per-layer and inter-layer cost
│   ├── overhead.py             # L0-L4 layer-by-layer overhead (Mode A + Mode B)
│   ├── read_throughput.py      # Peak read throughput ceiling (single snapshot, N reads)
│   ├── profile.py              # L0-L4 cProfile profiling
│   └── raw_tkv.py              # Raw TKV RocksDB baseline (absolute storage floor)
│
├── point/                      # Point benchmarks -- isolate one everybase dimension
│   ├── 00_flat_writes.py       # Flat shape write throughput
│   ├── 01_nested_nav.py        # Nested shape navigation at depth 2/4/6
│   ├── 02_dict_shapes.py       # Dict-of-Shapes CRUD
│   ├── 03_list_ops.py          # ListRef store/append/iteration
│   ├── 04_atomic_granularity.py  # auto_atomic vs manual Atomic vs batched
│   ├── run_all.py              # Run all point benchmarks
│   └── RESULTS.md              # Point benchmark results
│
└── scenarios/                  # Scenario benchmarks -- real-world patterns
    ├── 00_user_database.py     # 10 users x (5 fields + 10 tags)
    └── 01_market.py            # 5 categories x 10 products x 4 fields
```

## Measurement Dimensions

Every benchmark result is shaped by three independent dimensions. Mixing them
silently produces misleading numbers. Each benchmark must be explicit about
where it sits on each axis.

### 1. Transaction granularity

How many operations share one transaction/snapshot boundary.

| Label | Pattern | What it measures |
|-------|---------|------------------|
| **1 txn** | open txn, N ops, commit | Pure per-layer code cost. Txn overhead amortized to ~zero. |
| **1 txn/op** | for each op: open txn, 1 op, commit | Real-world single-op cost. Txn open/close/commit included. |

Layer benchmarks run both as **Mode A** (1 txn) and **Mode B** (1 txn/op).

The difference between Mode A and Mode B *for the same layer* reveals how much
of the per-op cost is transaction overhead vs actual layer code.

### 2. Operation scope

What work is included in the timed region beyond the raw read/write.

| Label | What's inside the timed loop | Example |
|-------|------------------------------|---------|
| **pure op** | Only the get/put call itself | `root.put_child_primitive(key, val)` with `root` already resolved |
| **init + op** | Container/View/Shape resolution + the op | `Container.get(path, tx)` then `put_child_primitive(...)` |
| **full execute** | Term tree `.execute(ctx)` which opens span, resolves view, does op, commits | `Atomic(Shape.field.set(v)).execute(ctx)` |

Higher layers inherently bundle more init work — you can't call
`DictView.__setitem__` without first calling `open_root()`, and you can't use
Shape without `Atomic.execute()`. So the scope is dictated by the layer's API.
Be explicit about what's included.

At L2+, "init + op" is the natural unit. At L4, "full execute" is the only
meaningful unit — the term tree is the API.

### 3. Tree construction vs execution

Term trees (`Atomic(Seq(Shape.f.set(v), ...))`) have two costs:

| Phase | What happens | When to measure |
|-------|-------------|-----------------|
| **Construction** | Python objects allocated, tree assembled | Once at startup (or once per unique operation) |
| **Execution** | `.execute(ctx)` — opens spans, resolves storage, does I/O, commits | Every call |

All benchmarks in this suite **pre-build trees** outside the timed section.
Loops measure execution only. This matters because construction is a one-time
cost in real usage (trees are typically built once, executed many times).

If a benchmark *does* include construction in the loop, it must say so
explicitly — otherwise results are contaminated by Python object allocation
that wouldn't occur in real workloads.

### Reading results with these dimensions

When comparing two numbers, check all three axes match. For example:

- "L4 is 14x slower than L0" — only meaningful if both use the same txn
  granularity. Mode A (1 txn) gives the pure layer overhead; Mode B (1 txn/op)
  adds txn cost that may dominate at lower layers.
- "auto_atomic is 2x slower than manual Atomic" — because auto_atomic uses
  1 txn/op while manual Atomic batches into 1 txn. The layer code is identical;
  the txn granularity drives the difference.
- "10 separate Atomics vs 1 batched Atomic" — same layer, same ops, different
  txn granularity. The delta is pure txn overhead x9.

## Suites

### Layers (`layers/`)

Layer-by-layer overhead analysis. Measures put/get cost at each abstraction layer (L0 rdbpy -> L1 tkv -> L2 container -> L3 dictview -> L4 shape/atomic) to show where overhead lives. Includes raw TKV baseline for absolute storage floor.

Note: layers are not strictly stacked. L4 (Shape) uses its own code path through containers, it does NOT go through L3 (DictView). Each layer measurement uses that layer's native API.

### Point (`point/`)

Everybase-layer-only benchmarks. Each isolates one exact aspect of the shape/term API -- flat writes, nesting depth, dict/list operations, atomic wrapping strategies. All term trees are pre-built; loops measure only `.execute(ctx)`.

### Scenarios (`scenarios/`)

Real-world usage patterns. Shapes -> data -> trees (pre-built) -> benchmark (execution only). Trees are constructed once; only `.execute(ctx)` is timed. Holistic view of full-stack performance.

## Quick Start

```bash
# Layers -- overhead, throughput, profiling
uv run python benchmarks/layers/overhead.py
uv run python benchmarks/layers/read_throughput.py
uv run python benchmarks/layers/profile.py
uv run python benchmarks/layers/raw_tkv.py

# Point -- all scenarios
uv run python benchmarks/point/run_all.py

# Point -- single scenario
uv run python benchmarks/point/00_flat_writes.py

# Scenarios
uv run python benchmarks/scenarios/00_user_database.py
uv run python benchmarks/scenarios/01_market.py
```

## Instrumentation

`utils.py` provides monkey-patching counters for key subsystems:

- `storage.begin_transaction` / `storage.begin_snapshot` -- transaction open count
- `rocksdb.get` / `rocksdb.put` / `rocksdb.scan` / `rocksdb.commit` -- storage I/O
- `virtuals.create_container` / `virtuals.get_node_info` / `virtuals.node_exists` -- virtuals container ops
- `observer.notify` -- observer notification count

Each benchmark reports wall time, per-op latency, ops/sec, and all counter values. L0 (raw rdbpy) bypasses the monkey-patched tkv layer, so its counters show 0.
