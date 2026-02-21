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
├── point/                      # Point benchmarks -- isolate one dimension
│   ├── 01_flat_writes.py       # Flat shape write throughput
│   ├── 02_nested_nav.py        # Nested shape navigation at depth 2/4/6
│   ├── 03_dict_shapes.py       # Dict-of-Shapes CRUD
│   ├── 04_list_ops.py          # ListRef store/append/iteration
│   ├── 05_mixed_flow.py        # Mixed read/write with term resolution
│   ├── 06_atomic_granularity.py  # auto_atomic vs manual Atomic vs raw
│   ├── 07_observer_overhead.py   # Observer enabled vs disabled
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

Clinical, single-dimension benchmarks. Each isolates one exact aspect -- flat writes, nesting depth, dict/list operations, atomic granularity, observer cost. Used to find bottlenecks.

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
uv run python benchmarks/point/01_flat_writes.py

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
