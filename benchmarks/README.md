# Everybase Benchmarks

Benchmarking suite for the everybase data layer (pv + everypv + everyshape) and term tree execution.

## Structure

```
benchmarks/
├── utils.py                    # Shared: counters, timed_run, reporting
│
├── layers/                     # Layer benchmarks -- isolate per-layer and inter-layer cost
│   ├── 00_overhead.py          # L0-L4 layer-by-layer overhead measurement
│   ├── 01_profile.py           # L0-L4 cProfile profiling
│   ├── 02_raw_tkv.py           # Raw TKV RocksDB baseline (absolute storage floor)
│   └── RESULTS.md              # Layer overhead results
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

## Suites

### Layers (`layers/`)

Layer-by-layer overhead analysis. Measures put/get cost at each abstraction layer (L0 rdbpy -> L1 tkv -> L2 container -> L3 dictview -> L4 shape/atomic) to show where overhead lives. Includes raw TKV baseline for absolute storage floor.

### Point (`point/`)

Everybase-layer-only benchmarks. Each isolates one exact aspect of the shape/term API -- flat writes, nesting depth, dict/list operations, atomic wrapping strategies. All term trees are pre-built; loops measure only `.execute(ctx)`.

### Scenarios (`scenarios/`)

Real-world usage patterns. Shapes -> data -> trees (pre-built) -> benchmark (execution only). Trees are constructed once; only `.execute(ctx)` is timed. Holistic view of full-stack performance.

## Quick Start

```bash
# Layers -- overhead and profiling
uv run python benchmarks/layers/00_overhead.py
uv run python benchmarks/layers/01_profile.py
uv run python benchmarks/layers/02_raw_tkv.py

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
- `pv.create_container` / `pv.get_node_info` / `pv.node_exists` -- PV container ops
- `observer.notify` -- observer notification count

Each benchmark reports wall time, per-op latency, ops/sec, and all counter values.
