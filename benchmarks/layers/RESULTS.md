# Layer-by-Layer Overhead (L0-L4)

N = 500 ops per benchmark

## PUT -- layer progression

| Layer | Scenario | per-op (ms) | ops/s | vs L0 | delta (ms) |
|-------|----------|-------------|-------|-------|------------|
| L0 | L0 rdbpy put x500 | 0.0207 | 48,201 | 1.0x | +0.0207 |
| L1 | L1 tkv put x500 | 0.0400 | 24,986 | 1.9x | +0.0193 |
| L2 | L2 container put x500 | 0.0817 | 12,244 | 3.9x | +0.0417 |
| L3 | L3 dictview put x500 | 0.1156 | 8,651 | 5.6x | +0.0339 |
| L4 | L4 shape put x500 | 0.1222 | 8,186 | 5.9x | +0.0066 |

## GET -- layer progression

| Layer | Scenario | per-op (ms) | ops/s | vs L0 | delta (ms) |
|-------|----------|-------------|-------|-------|------------|
| L0 | L0 rdbpy get x500 | 0.0035 | 282,515 | 1.0x | +0.0035 |
| L1 | L1 tkv get x500 | 0.0111 | 89,792 | 3.1x | +0.0076 |
| L2 | L2 container get x500 | 0.0307 | 32,582 | 8.7x | +0.0196 |
| L3 | L3 dictview get x500 | 0.0241 | 41,522 | 6.8x | +-0.0066 |
| L4 | L4 shape get x500 | 0.0582 | 17,182 | 16.4x | +0.0341 |

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
