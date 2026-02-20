# Everybase Data Layer Benchmarks

Thorough benchmarking of the everybase data layer (pv + everypv + everyshape) and term tree execution.
Fixed RocksDB storage + InMemory observer.
Measures raw compute and disk I/O costs across different scenarios and data dimensions.

## Quick Start

```bash
# Run all scenarios
uv run python benchmarks/run_all.py

# Run a single scenario
uv run python benchmarks/00_raw_tkv.py
```

Results are written to `benchmarks/RESULTS.md`.

## Scenarios

| File | Scenario | What it isolates |
|------|----------|-----------------|
| `00_raw_tkv.py` | Raw TKV RocksDB | Absolute storage floor — pure get/put/commit, no PV or terms |
| `01_flat_writes.py` | Flat Writes | auto_atomic overhead, RocksDB put, container create for flat shapes |
| `02_nested_nav.py` | Nested Shape Navigation | get_node_info, ensure_created, path navigation at depth 2/4/6 |
| `03_dict_shapes.py` | Dict-of-Shapes CRUD | ShapesDictRef store, container creation, scan/iteration at 10/100/500 entries |
| `04_list_ops.py` | List Append & Iteration | ListRef store/append, iter_children, extraction at 10/100/500 items |
| `05_mixed_flow.py` | Mixed Read/Write Flow | Full stack: term resolution + FuncCallOp + auto_atomic + observer |
| `06_atomic_granularity.py` | Auto-Atomic Granularity | Per-term auto_atomic vs manual Atomic vs raw DictView vs batched |
| `07_observer_overhead.py` | Observer Overhead | InMemoryObserver enabled vs disabled, term vs raw DictView |

## Instrumentation

`utils.py` provides monkey-patching counters for key subsystems:

- `storage.begin_transaction` / `storage.begin_snapshot` — transaction open count
- `rocksdb.get` / `rocksdb.put` / `rocksdb.scan` / `rocksdb.commit` — storage I/O
- `pv.create_container` / `pv.get_node_info` / `pv.node_exists` — PV container ops
- `observer.notify` — observer notification count

Each scenario reports wall time, per-op latency, ops/sec, and all counter values.

## Key Findings

For a 5-field write operation:

| Layer | ops/sec | per-op | overhead vs raw tkv |
|-------|---------|--------|---------------------|
| Raw TKV RocksDB (per-op txn) | ~9K | ~0.12ms | 1x |
| Raw TKV RocksDB (single txn) | ~33K | ~0.03ms | — |
| Raw DictView (PV containers) | ~2.5K | ~0.4ms | ~3x |
| Single Atomic (term tree) | ~1.7K | ~0.6ms | ~5x |
| auto_atomic per-term | ~900 | ~1.1ms | ~10x |

Main bottlenecks:
1. **Transaction granularity** — auto_atomic wraps each Term individually, opening 5x more txns than needed
2. **Read amplification** — every write does ~4 gets for container existence/parent chain validation
3. **Container creation** — ensure_created runs on every field write even when container exists
