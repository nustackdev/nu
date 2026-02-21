# Scenario 8: Layer-by-Layer Overhead

N = 500 ops per benchmark

## PUT — layer progression

| Layer | Scenario | per-op (ms) | ops/s | vs L0 | delta (ms) |
|-------|----------|-------------|-------|-------|------------|
| L0 | L0 rdbpy put x500 | 0.0231 | 43,202 | 1.0x | +0.0231 |
| L1 | L1 tkv put x500 | 0.0612 | 16,346 | 2.6x | +0.0380 |
| L2 | L2 container put x500 | 0.1037 | 9,642 | 4.5x | +0.0425 |
| L3 | L3 dictview put x500 | 0.1558 | 6,420 | 6.7x | +0.0520 |
| L4 | L4 shape put x500 | 0.2138 | 4,677 | 9.2x | +0.0580 |

## GET — layer progression

| Layer | Scenario | per-op (ms) | ops/s | vs L0 | delta (ms) |
|-------|----------|-------------|-------|-------|------------|
| L0 | L0 rdbpy get x500 | 0.0052 | 193,285 | 1.0x | +0.0052 |
| L1 | L1 tkv get x500 | 0.0221 | 45,289 | 4.3x | +0.0169 |
| L2 | L2 container get x500 | 0.0422 | 23,671 | 8.2x | +0.0202 |
| L3 | L3 dictview get x500 | 0.0597 | 16,753 | 11.5x | +0.0174 |
| L4 | L4 shape get x500 | 0.1167 | 8,572 | 22.5x | +0.0570 |

## PUT counters

| Scenario | pv.create_container | rocksdb.commit | rocksdb.get | rocksdb.put | storage.begin_transaction |
|----------|---:|---:|---:|---:|---:|
| L0 rdbpy put x500 | 0 | 0 | 0 | 0 | 0 |
| L1 tkv put x500 | 0 | 500 | 0 | 500 | 500 |
| L2 container put x500 | 0 | 500 | 1500 | 500 | 500 |
| L3 dictview put x500 | 500 | 500 | 2500 | 1000 | 500 |
| L4 shape put x500 | 500 | 500 | 2000 | 500 | 500 |

## GET counters

| Scenario | pv.get_node_info | rocksdb.get | storage.begin_snapshot |
|----------|---:|---:|---:|
| L0 rdbpy get x500 | 0 | 0 | 0 |
| L1 tkv get x500 | 0 | 500 | 500 |
| L2 container get x500 | 0 | 1000 | 500 |
| L3 dictview get x500 | 500 | 500 | 500 |
| L4 shape get x500 | 500 | 500 | 500 |

## L5: Nested shape scenarios

| Scenario | N ops | Wall (s) | Per-op (ms) | ops/s |
|----------|-------|----------|-------------|-------|
| L5 put flat Root.val x500 | 500 | 0.0908 | 0.182 | 5,504 |
| L5 get flat Root.val x500 | 500 | 0.0378 | 0.076 | 13,238 |
| L5 put flat Root.label x500 | 500 | 0.0756 | 0.151 | 6,618 |
| L5 get flat Root.label x500 | 500 | 0.0365 | 0.073 | 13,704 |
| L5 put depth-1 a.val x500 | 500 | 0.0919 | 0.184 | 5,438 |
| L5 get depth-1 a.val x500 | 500 | 0.0500 | 0.100 | 10,007 |
| L5 put depth-2 a.b.val x500 | 500 | 0.1000 | 0.200 | 4,999 |
| L5 get depth-2 a.b.val x500 | 500 | 0.0600 | 0.120 | 8,327 |
| L5 put depth-3 a.b.c.val x500 | 500 | 0.1112 | 0.222 | 4,496 |
| L5 get depth-3 a.b.c.val x500 | 500 | 0.0691 | 0.138 | 7,234 |
| L5 put depth-3 a.b.c.tag x500 | 500 | 0.1126 | 0.225 | 4,441 |
| L5 get depth-3 a.b.c.tag x500 | 500 | 0.0700 | 0.140 | 7,139 |
| L5 put dict items[k0] x500 | 500 | 0.0834 | 0.167 | 5,997 |
| L5 get dict items[k0] x500 | 500 | 0.0426 | 0.085 | 11,737 |
| L5 put dict items[k1] x500 | 500 | 0.0840 | 0.168 | 5,955 |
| L5 get dict items[k1] x500 | 500 | 0.0426 | 0.085 | 11,729 |
| L5 put set a.b.c / get a x500 | 500 | 0.1116 | 0.223 | 4,481 |
| L5 get set a.b.c / get a x500 | 500 | 0.0477 | 0.095 | 10,478 |
| L5 put set flat / get deep x500 | 500 | 0.0778 | 0.156 | 6,428 |
| L5 get set flat / get deep x500 | 500 | 0.0678 | 0.136 | 7,377 |

### L5 counters

| Scenario | pv.create_container | pv.get_node_info | rocksdb.commit | rocksdb.get | rocksdb.put | storage.begin_snapshot | storage.begin_transaction |
|----------|---:|---:|---:|---:|---:|---:|---:|
| L5 put flat Root.val x500 | 500 | 0 | 500 | 2000 | 500 | 0 | 500 |
| L5 get flat Root.val x500 | 0 | 500 | 0 | 500 | 0 | 500 | 0 |
| L5 put flat Root.label x500 | 500 | 0 | 500 | 2000 | 500 | 0 | 500 |
| L5 get flat Root.label x500 | 0 | 500 | 0 | 500 | 0 | 500 | 0 |
| L5 put depth-1 a.val x500 | 500 | 0 | 500 | 2000 | 500 | 0 | 500 |
| L5 get depth-1 a.val x500 | 0 | 500 | 0 | 500 | 0 | 500 | 0 |
| L5 put depth-2 a.b.val x500 | 500 | 0 | 500 | 2000 | 500 | 0 | 500 |
| L5 get depth-2 a.b.val x500 | 0 | 500 | 0 | 500 | 0 | 500 | 0 |
| L5 put depth-3 a.b.c.val x500 | 500 | 0 | 500 | 2000 | 500 | 0 | 500 |
| L5 get depth-3 a.b.c.val x500 | 0 | 500 | 0 | 500 | 0 | 500 | 0 |
| L5 put depth-3 a.b.c.tag x500 | 500 | 0 | 500 | 2000 | 500 | 0 | 500 |
| L5 get depth-3 a.b.c.tag x500 | 0 | 500 | 0 | 500 | 0 | 500 | 0 |
| L5 put dict items[k0] x500 | 500 | 0 | 500 | 2000 | 500 | 0 | 500 |
| L5 get dict items[k0] x500 | 0 | 500 | 0 | 500 | 0 | 500 | 0 |
| L5 put dict items[k1] x500 | 500 | 0 | 500 | 2000 | 500 | 0 | 500 |
| L5 get dict items[k1] x500 | 0 | 500 | 0 | 500 | 0 | 500 | 0 |
| L5 put set a.b.c / get a x500 | 500 | 0 | 500 | 2000 | 500 | 0 | 500 |
| L5 get set a.b.c / get a x500 | 0 | 500 | 0 | 500 | 0 | 500 | 0 |
| L5 put set flat / get deep x500 | 500 | 0 | 500 | 2000 | 500 | 0 | 500 |
| L5 get set flat / get deep x500 | 0 | 500 | 0 | 500 | 0 | 500 | 0 |

## Interpretation

Each layer row shows:
- **per-op (ms)**: average wall time per single put or get
- **vs L0**: slowdown factor relative to raw rdbpy
- **delta (ms)**: marginal cost added by *this* layer alone

The delta column reveals where overhead actually lives.
L5 scenarios show that nesting depth has near-zero marginal cost
once the first container exists — the dominant cost is transaction
setup and term tree execution, not path navigation.
