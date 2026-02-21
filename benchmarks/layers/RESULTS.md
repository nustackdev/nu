# Layer-by-Layer Overhead (L0-L4)

N sizes: 100, 1,000, 10,000

## N = 100

### Mode A: Pure R/W (1 txn, N ops)

Transaction opened ONCE, all ops inside, commit ONCE.

#### PUT

| Layer | Scenario | per-op (ms) | ops/s | vs L0 |
|-------|----------|-------------|-------|-------|
| L0 | L0 rdbpy put x100 [1txn] | 0.0198 | 50,415 | 1.0x |
| L1 | L1 tkv put x100 [1txn] | 0.0092 | 108,640 | 0.5x |
| L2 | L2 container put x100 [1txn] | 0.0218 | 45,956 | 1.1x |
| L3 | L3 dictview put x100 [1txn] | 0.0853 | 11,729 | 4.3x |
| L4 | L4 shape put x100 [1txn] | 0.0717 | 13,948 | 3.6x |

#### GET

| Layer | Scenario | per-op (ms) | ops/s | vs L0 |
|-------|----------|-------------|-------|-------|
| L0 | L0 rdbpy get x100 [1snap] | 0.0018 | 544,689 | 1.0x |
| L1 | L1 tkv get x100 [1snap] | 0.0043 | 230,098 | 2.4x |
| L2 | L2 container get x100 [1snap] | 0.0065 | 154,163 | 3.5x |
| L3 | L3 dictview get x100 [1snap] | 0.0055 | 182,298 | 3.0x |
| L4 | L4 shape get x100 [1snap] | 0.0209 | 47,870 | 11.4x |

### Mode B: Per-op cost (N txns, N ops)

One txn per operation. Real-world single-op cost.

#### PUT

| Layer | Scenario | per-op (ms) | ops/s | vs L0 |
|-------|----------|-------------|-------|-------|
| L0 | L0 rdbpy put x100 [1txn/op] | 0.0208 | 48,029 | 1.0x |
| L1 | L1 tkv put x100 [1txn/op] | 0.0584 | 17,138 | 2.8x |
| L2 | L2 container put x100 [1txn/op] | 0.0843 | 11,860 | 4.0x |
| L3 | L3 dictview put x100 [1txn/op] | 0.1360 | 7,351 | 6.5x |
| L4 | L4 shape put x100 [1txn/op] | 0.1541 | 6,487 | 7.4x |

#### GET

| Layer | Scenario | per-op (ms) | ops/s | vs L0 |
|-------|----------|-------------|-------|-------|
| L0 | L0 rdbpy get x100 [1snap/op] | 0.0102 | 97,985 | 1.0x |
| L1 | L1 tkv get x100 [1snap/op] | 0.0138 | 72,450 | 1.4x |
| L2 | L2 container get x100 [1snap/op] | 0.0283 | 35,311 | 2.8x |
| L3 | L3 dictview get x100 [1snap/op] | 0.0216 | 46,244 | 2.1x |
| L4 | L4 shape get x100 [1snap/op] | 0.0526 | 19,016 | 5.2x |

## N = 1,000

### Mode A: Pure R/W (1 txn, N ops)

Transaction opened ONCE, all ops inside, commit ONCE.

#### PUT

| Layer | Scenario | per-op (ms) | ops/s | vs L0 |
|-------|----------|-------------|-------|-------|
| L0 | L0 rdbpy put x1000 [1txn] | 0.0032 | 312,675 | 1.0x |
| L1 | L1 tkv put x1000 [1txn] | 0.0048 | 207,511 | 1.5x |
| L2 | L2 container put x1000 [1txn] | 0.0709 | 14,106 | 22.2x |
| L3 | L3 dictview put x1000 [1txn] | 0.0554 | 18,048 | 17.3x |
| L4 | L4 shape put x1000 [1txn] | 0.1165 | 8,583 | 36.4x |

#### GET

| Layer | Scenario | per-op (ms) | ops/s | vs L0 |
|-------|----------|-------------|-------|-------|
| L0 | L0 rdbpy get x1000 [1snap] | 0.0010 | 1,033,299 | 1.0x |
| L1 | L1 tkv get x1000 [1snap] | 0.0029 | 340,360 | 3.0x |
| L2 | L2 container get x1000 [1snap] | 0.0069 | 145,475 | 7.1x |
| L3 | L3 dictview get x1000 [1snap] | 0.0045 | 224,044 | 4.6x |
| L4 | L4 shape get x1000 [1snap] | 0.0158 | 63,483 | 16.3x |

### Mode B: Per-op cost (N txns, N ops)

One txn per operation. Real-world single-op cost.

#### PUT

| Layer | Scenario | per-op (ms) | ops/s | vs L0 |
|-------|----------|-------------|-------|-------|
| L0 | L0 rdbpy put x1000 [1txn/op] | 0.0197 | 50,781 | 1.0x |
| L1 | L1 tkv put x1000 [1txn/op] | 0.0400 | 25,009 | 2.0x |
| L2 | L2 container put x1000 [1txn/op] | 0.0810 | 12,347 | 4.1x |
| L3 | L3 dictview put x1000 [1txn/op] | 0.2580 | 3,876 | 13.1x |
| L4 | L4 shape put x1000 [1txn/op] | 0.1482 | 6,750 | 7.5x |

#### GET

| Layer | Scenario | per-op (ms) | ops/s | vs L0 |
|-------|----------|-------------|-------|-------|
| L0 | L0 rdbpy get x1000 [1snap/op] | 0.0041 | 244,287 | 1.0x |
| L1 | L1 tkv get x1000 [1snap/op] | 0.0108 | 92,562 | 2.6x |
| L2 | L2 container get x1000 [1snap/op] | 0.0284 | 35,271 | 6.9x |
| L3 | L3 dictview get x1000 [1snap/op] | 0.0298 | 33,539 | 7.3x |
| L4 | L4 shape get x1000 [1snap/op] | 0.0512 | 19,542 | 12.5x |

## N = 10,000

### Mode A: Pure R/W (1 txn, N ops)

Transaction opened ONCE, all ops inside, commit ONCE.

#### PUT

| Layer | Scenario | per-op (ms) | ops/s | vs L0 |
|-------|----------|-------------|-------|-------|
| L0 | L0 rdbpy put x10000 [1txn] | 0.0033 | 305,093 | 1.0x |
| L1 | L1 tkv put x10000 [1txn] | 0.0048 | 210,249 | 1.5x |
| L2 | L2 container put x10000 [1txn] | 0.0186 | 53,741 | 5.7x |
| L3 | L3 dictview put x10000 [1txn] | 0.0574 | 17,428 | 17.5x |
| L4 | L4 shape put x10000 [1txn] | 0.0458 | 21,848 | 14.0x |

#### GET

| Layer | Scenario | per-op (ms) | ops/s | vs L0 |
|-------|----------|-------------|-------|-------|
| L0 | L0 rdbpy get x10000 [1snap] | 0.0009 | 1,068,802 | 1.0x |
| L1 | L1 tkv get x10000 [1snap] | 0.0021 | 465,412 | 2.3x |
| L2 | L2 container get x10000 [1snap] | 0.0054 | 186,357 | 5.7x |
| L3 | L3 dictview get x10000 [1snap] | 0.0041 | 242,487 | 4.4x |
| L4 | L4 shape get x10000 [1snap] | 0.0125 | 79,754 | 13.4x |

### Mode B: Per-op cost (N txns, N ops)

One txn per operation. Real-world single-op cost.

#### PUT

| Layer | Scenario | per-op (ms) | ops/s | vs L0 |
|-------|----------|-------------|-------|-------|
| L0 | L0 rdbpy put x10000 [1txn/op] | 0.0151 | 66,227 | 1.0x |
| L1 | L1 tkv put x10000 [1txn/op] | 0.0296 | 33,759 | 2.0x |
| L2 | L2 container put x10000 [1txn/op] | 0.0729 | 13,719 | 4.8x |
| L3 | L3 dictview put x10000 [1txn/op] | 0.1002 | 9,979 | 6.6x |
| L4 | L4 shape put x10000 [1txn/op] | 0.1108 | 9,028 | 7.3x |

#### GET

| Layer | Scenario | per-op (ms) | ops/s | vs L0 |
|-------|----------|-------------|-------|-------|
| L0 | L0 rdbpy get x10000 [1snap/op] | 0.0035 | 284,425 | 1.0x |
| L1 | L1 tkv get x10000 [1snap/op] | 0.0084 | 118,645 | 2.4x |
| L2 | L2 container get x10000 [1snap/op] | 0.0220 | 45,430 | 6.3x |
| L3 | L3 dictview get x10000 [1snap/op] | 0.0173 | 57,964 | 4.9x |
| L4 | L4 shape get x10000 [1snap/op] | 0.0421 | 23,762 | 12.0x |

## Notes

- L0 counters show 0 because rdbpy bypasses monkey-patched tkv layer
- Layers are not strictly stacked: L4 (Shape) does NOT go through L3 (DictView)
- Each layer uses its own API path, so deltas show marginal cost of that API
- Mode A delta = pure code overhead; Mode B delta = code + txn overhead
