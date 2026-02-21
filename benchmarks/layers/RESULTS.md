# Layer-by-Layer Overhead (L0-L4)

N = 500 ops per benchmark

## PUT — layer progression

| Layer | Scenario | per-op (ms) | ops/s | vs L0 | delta (ms) |
|-------|----------|-------------|-------|-------|------------|
| L0 | L0 rdbpy put x500 | 0.0240 | 41,652 | 1.0x | +0.0240 |
| L1 | L1 tkv put x500 | 0.0429 | 23,310 | 1.8x | +0.0189 |
| L2 | L2 container put x500 | 0.0877 | 11,402 | 3.7x | +0.0448 |
| L3 | L3 dictview put x500 | 0.1107 | 9,035 | 4.6x | +0.0230 |
| L4 | L4 shape put x500 | 0.1182 | 8,460 | 4.9x | +0.0075 |

## GET — layer progression

| Layer | Scenario | per-op (ms) | ops/s | vs L0 | delta (ms) |
|-------|----------|-------------|-------|-------|------------|
| L0 | L0 rdbpy get x500 | 0.0047 | 211,183 | 1.0x | +0.0047 |
| L1 | L1 tkv get x500 | 0.0137 | 72,788 | 2.9x | +0.0090 |
| L2 | L2 container get x500 | 0.0297 | 33,615 | 6.3x | +0.0160 |
| L3 | L3 dictview get x500 | 0.0212 | 47,276 | 4.5x | +-0.0086 |
| L4 | L4 shape get x500 | 0.0551 | 18,157 | 11.6x | +0.0339 |

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
