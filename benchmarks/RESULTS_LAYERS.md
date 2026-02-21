# Layer-by-Layer Overhead (L0–L4)

N = 500 ops per benchmark

## PUT — layer progression

| Layer | Scenario | per-op (ms) | ops/s | vs L0 | delta (ms) |
|-------|----------|-------------|-------|-------|------------|
| L0 | L0 rdbpy put x500 | 0.0246 | 40,608 | 1.0x | +0.0246 |
| L1 | L1 tkv put x500 | 0.0387 | 25,821 | 1.6x | +0.0141 |
| L2 | L2 container put x500 | 0.0937 | 10,669 | 3.8x | +0.0550 |
| L3 | L3 dictview put x500 | 0.1220 | 8,195 | 5.0x | +0.0283 |
| L4 | L4 shape put x500 | 0.1451 | 6,894 | 5.9x | +0.0230 |

## GET — layer progression

| Layer | Scenario | per-op (ms) | ops/s | vs L0 | delta (ms) |
|-------|----------|-------------|-------|-------|------------|
| L0 | L0 rdbpy get x500 | 0.0052 | 192,994 | 1.0x | +0.0052 |
| L1 | L1 tkv get x500 | 0.0141 | 70,872 | 2.7x | +0.0089 |
| L2 | L2 container get x500 | 0.0298 | 33,568 | 5.7x | +0.0157 |
| L3 | L3 dictview get x500 | 0.0390 | 25,647 | 7.5x | +0.0092 |
| L4 | L4 shape get x500 | 0.0583 | 17,145 | 11.3x | +0.0193 |

## PUT counters

| Scenario | pv.create_container | rocksdb.commit | rocksdb.get | rocksdb.put | storage.begin_transaction |
|----------|---:|---:|---:|---:|---:|
| L0 rdbpy put x500 | 0 | 0 | 0 | 0 | 0 |
| L1 tkv put x500 | 0 | 500 | 0 | 500 | 500 |
| L2 container put x500 | 0 | 500 | 1500 | 500 | 500 |
| L3 dictview put x500 | 500 | 500 | 1500 | 1000 | 500 |
| L4 shape put x500 | 500 | 500 | 1000 | 500 | 500 |

## GET counters

| Scenario | pv.get_node_info | rocksdb.get | storage.begin_snapshot |
|----------|---:|---:|---:|
| L0 rdbpy get x500 | 0 | 0 | 0 |
| L1 tkv get x500 | 0 | 500 | 500 |
| L2 container get x500 | 0 | 1000 | 500 |
| L3 dictview get x500 | 500 | 500 | 500 |
| L4 shape get x500 | 500 | 500 | 500 |

## Interpretation

Each layer row shows:
- **per-op (ms)**: average wall time per single put or get
- **vs L0**: slowdown factor relative to raw rdbpy
- **delta (ms)**: marginal cost added by *this* layer alone

The delta column reveals where overhead actually lives.
