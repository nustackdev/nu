# Everybase Data Layer Benchmark Results

**Date:** 2026-02-20 20:13:44
**Total runtime:** 9.9s
**Python:** 3.12.2

---

## Scenario 0: Raw TKV RocksDB

### Timing

| Scenario | N ops | Wall (s) | Per-op (ms) | ops/s |
|----------|-------|----------|-------------|-------|
| raw_put_1key x1000 | 1,000 | 0.0579 | 0.058 | 17,261 |
| raw_put_5keys x1000 | 1,000 | 0.0781 | 0.078 | 12,797 |
| raw_overwrite_5keys x1000 | 1,000 | 0.0764 | 0.076 | 13,085 |
| raw_get_5keys x1000 | 1,000 | 0.0296 | 0.030 | 33,768 |
| raw_put_5keys_1txn x1000 | 1,000 | 0.0279 | 0.028 | 35,846 |

### Counters

| Scenario | rocksdb.commit | rocksdb.get | rocksdb.put | storage.begin_snapshot | storage.begin_transaction |
|----------|---:|---:|---:|---:|---:|
| raw_put_1key x1000 | 1000 | 0 | 1000 | 0 | 1000 |
| raw_put_5keys x1000 | 1000 | 0 | 5000 | 0 | 1000 |
| raw_overwrite_5keys x1000 | 1000 | 0 | 5000 | 0 | 1000 |
| raw_get_5keys x1000 | 0 | 5000 | 0 | 1000 | 0 |
| raw_put_5keys_1txn x1000 | 1 | 0 | 5000 | 0 | 1 |

---

## Scenario 1: Flat Writes

### Timing

| Scenario | N ops | Wall (s) | Per-op (ms) | ops/s |
|----------|-------|----------|-------------|-------|
| single_field x100 | 100 | 0.0260 | 0.260 | 3,848 |
| 10_fields_separate_atomic x100 | 100 | 0.1997 | 1.997 | 501 |
| 10_fields_single_atomic x100 | 100 | 0.0913 | 0.913 | 1,095 |
| 10_fields_auto_atomic x100 | 100 | 0.1938 | 1.938 | 516 |

### Counters

| Scenario | pv.create_container | rocksdb.commit | rocksdb.get | rocksdb.put | storage.begin_transaction |
|----------|---:|---:|---:|---:|---:|
| single_field x100 | 100 | 100 | 400 | 100 | 100 |
| 10_fields_separate_atomic x100 | 1000 | 1000 | 4009 | 1009 | 1000 |
| 10_fields_single_atomic x100 | 1000 | 100 | 4000 | 1000 | 100 |
| 10_fields_auto_atomic x100 | 1000 | 1000 | 4000 | 1000 | 1000 |

---

## Scenario 2: Nested Shape Navigation

### Timing

| Scenario | N ops | Wall (s) | Per-op (ms) | ops/s |
|----------|-------|----------|-------------|-------|
| depth_2_write x100 | 100 | 0.0326 | 0.326 | 3,070 |
| depth_4_write x100 | 100 | 0.0343 | 0.343 | 2,913 |
| depth_6_write x100 | 100 | 0.0335 | 0.335 | 2,985 |
| depth_2_read x100 | 100 | 0.0129 | 0.129 | 7,726 |
| depth_4_read x100 | 100 | 0.0191 | 0.191 | 5,225 |
| depth_6_read x100 | 100 | 0.0232 | 0.232 | 4,304 |

### Counters

| Scenario | pv.create_container | pv.get_node_info | rocksdb.commit | rocksdb.get | rocksdb.put | storage.begin_snapshot | storage.begin_transaction |
|----------|---:|---:|---:|---:|---:|---:|---:|
| depth_2_write x100 | 100 | 0 | 100 | 400 | 100 | 0 | 100 |
| depth_4_write x100 | 100 | 0 | 100 | 400 | 100 | 0 | 100 |
| depth_6_write x100 | 100 | 0 | 100 | 400 | 100 | 0 | 100 |
| depth_2_read x100 | 0 | 100 | 0 | 100 | 0 | 100 | 0 |
| depth_4_read x100 | 0 | 100 | 0 | 100 | 0 | 100 | 0 |
| depth_6_read x100 | 0 | 100 | 0 | 100 | 0 | 100 | 0 |

---

## Scenario 3: Dict-of-Shapes CRUD

### Timing

| Scenario | N ops | Wall (s) | Per-op (ms) | ops/s |
|----------|-------|----------|-------------|-------|
| create_10_entries | 10 | 0.0071 | 0.706 | 1,417 |
| create_10_entries_batched | 10 | 0.0029 | 0.287 | 3,486 |
| read_10_entries_fields | 10 | 0.0042 | 0.417 | 2,400 |
| update_10_entries_1field | 10 | 0.0031 | 0.307 | 3,259 |
| create_100_entries | 100 | 0.0516 | 0.516 | 1,937 |
| create_100_entries_batched | 100 | 0.0251 | 0.251 | 3,983 |
| read_100_entries_fields | 100 | 0.0345 | 0.345 | 2,900 |
| update_100_entries_1field | 100 | 0.0250 | 0.250 | 3,995 |
| create_500_entries | 500 | 0.2009 | 0.402 | 2,489 |
| create_500_entries_batched | 500 | 0.1092 | 0.218 | 4,578 |
| read_500_entries_fields | 500 | 0.1761 | 0.352 | 2,839 |
| update_500_entries_1field | 500 | 0.1316 | 0.263 | 3,798 |

### Counters

| Scenario | pv.create_container | pv.get_node_info | rocksdb.commit | rocksdb.get | rocksdb.put | storage.begin_snapshot | storage.begin_transaction |
|----------|---:|---:|---:|---:|---:|---:|---:|
| create_10_entries | 40 | 22 | 10 | 132 | 52 | 0 | 10 |
| create_10_entries_batched | 40 | 20 | 1 | 130 | 50 | 0 | 1 |
| read_10_entries_fields | 0 | 30 | 0 | 30 | 0 | 10 | 0 |
| update_10_entries_1field | 10 | 0 | 10 | 40 | 10 | 0 | 10 |
| create_100_entries | 400 | 202 | 100 | 1302 | 502 | 0 | 100 |
| create_100_entries_batched | 400 | 200 | 1 | 1300 | 500 | 0 | 1 |
| read_100_entries_fields | 0 | 300 | 0 | 300 | 0 | 100 | 0 |
| update_100_entries_1field | 100 | 0 | 100 | 400 | 100 | 0 | 100 |
| create_500_entries | 2000 | 1002 | 500 | 6502 | 2502 | 0 | 500 |
| create_500_entries_batched | 2000 | 1000 | 1 | 6500 | 2500 | 0 | 1 |
| read_500_entries_fields | 0 | 1500 | 0 | 1500 | 0 | 500 | 0 |
| update_500_entries_1field | 500 | 0 | 500 | 2000 | 500 | 0 | 500 |

---

## Scenario 4: List Append & Iteration

### Timing

| Scenario | N ops | Wall (s) | Per-op (ms) | ops/s |
|----------|-------|----------|-------------|-------|
| store_list_int_10 | 1 | 0.0032 | 3.226 | 310 |
| store_list_str_10 | 1 | 0.0011 | 1.079 | 926 |
| read_list_int_10 | 1 | 0.0004 | 0.428 | 2,334 |
| read_by_index_10 | 10 | 0.0018 | 0.185 | 5,409 |
| append_one_by_one_10 | 10 | 0.0041 | 0.407 | 2,458 |
| store_list_int_100 | 1 | 0.0077 | 7.683 | 130 |
| store_list_str_100 | 1 | 0.0048 | 4.818 | 208 |
| read_list_int_100 | 1 | 0.0009 | 0.862 | 1,160 |
| read_by_index_100 | 100 | 0.0154 | 0.154 | 6,492 |
| append_one_by_one_100 | 100 | 0.0655 | 0.655 | 1,526 |
| store_list_int_500 | 1 | 0.0313 | 31.264 | 32 |
| store_list_str_500 | 1 | 0.0197 | 19.650 | 51 |
| read_list_int_500 | 1 | 0.0025 | 2.505 | 399 |
| read_by_index_500 | 500 | 0.0776 | 0.155 | 6,442 |
| append_one_by_one_500 | 500 | 0.8396 | 1.679 | 595 |

### Counters

| Scenario | pv.create_container | pv.get_node_info | rocksdb.commit | rocksdb.get | rocksdb.put | rocksdb.scan | storage.begin_snapshot | storage.begin_transaction |
|----------|---:|---:|---:|---:|---:|---:|---:|---:|
| store_list_int_10 | 11 | 2 | 1 | 34 | 14 | 1 | 0 | 1 |
| store_list_str_10 | 11 | 1 | 1 | 33 | 13 | 1 | 0 | 1 |
| read_list_int_10 | 0 | 0 | 0 | 1 | 0 | 1 | 1 | 0 |
| read_by_index_10 | 0 | 10 | 0 | 20 | 0 | 0 | 10 | 0 |
| append_one_by_one_10 | 10 | 0 | 10 | 50 | 20 | 10 | 0 | 10 |
| store_list_int_100 | 101 | 2 | 1 | 304 | 104 | 1 | 0 | 1 |
| store_list_str_100 | 101 | 1 | 1 | 303 | 103 | 1 | 0 | 1 |
| read_list_int_100 | 0 | 0 | 0 | 1 | 0 | 1 | 1 | 0 |
| read_by_index_100 | 0 | 100 | 0 | 200 | 0 | 0 | 100 | 0 |
| append_one_by_one_100 | 100 | 0 | 100 | 500 | 200 | 100 | 0 | 100 |
| store_list_int_500 | 501 | 2 | 1 | 1504 | 504 | 1 | 0 | 1 |
| store_list_str_500 | 501 | 1 | 1 | 1503 | 503 | 1 | 0 | 1 |
| read_list_int_500 | 0 | 0 | 0 | 1 | 0 | 1 | 1 | 0 |
| read_by_index_500 | 0 | 500 | 0 | 1000 | 0 | 0 | 500 | 0 |
| append_one_by_one_500 | 500 | 0 | 500 | 2500 | 1000 | 500 | 0 | 500 |

---

## Scenario 5: Mixed Read/Write Flow

### Timing

| Scenario | N ops | Wall (s) | Per-op (ms) | ops/s |
|----------|-------|----------|-------------|-------|
| mixed_manual_atomic x100 | 100 | 0.0997 | 0.997 | 1,003 |
| mixed_auto_atomic x100 | 100 | 0.1449 | 1.449 | 690 |
| read_heavy x100 | 100 | 0.0269 | 0.269 | 3,724 |

### Counters

| Scenario | pv.create_container | pv.get_node_info | rocksdb.commit | rocksdb.get | rocksdb.put | storage.begin_transaction |
|----------|---:|---:|---:|---:|---:|---:|
| mixed_manual_atomic x100 | 600 | 900 | 100 | 3300 | 600 | 100 |
| mixed_auto_atomic x100 | 600 | 900 | 600 | 3300 | 600 | 600 |
| read_heavy x100 | 100 | 200 | 100 | 600 | 100 | 100 |

---

## Scenario 6: Auto-Atomic Granularity

### Timing

| Scenario | N ops | Wall (s) | Per-op (ms) | ops/s |
|----------|-------|----------|-------------|-------|
| auto_atomic_per_term x200 | 200 | 0.2047 | 1.023 | 977 |
| single_atomic x200 | 200 | 0.1149 | 0.575 | 1,740 |
| raw_dictview x200 | 200 | 0.0611 | 0.305 | 3,276 |
| batched_auto_atomic_bs10 x200 | 200 | 0.0732 | 0.366 | 2,732 |
| batched_auto_atomic_bs50 x200 | 200 | 0.0706 | 0.353 | 2,834 |

### Counters

| Scenario | pv.create_container | rocksdb.commit | rocksdb.get | rocksdb.put | storage.begin_transaction |
|----------|---:|---:|---:|---:|---:|
| auto_atomic_per_term x200 | 1000 | 1000 | 4000 | 1000 | 1000 |
| single_atomic x200 | 1000 | 200 | 4000 | 1000 | 200 |
| raw_dictview x200 | 1000 | 200 | 4000 | 1000 | 200 |
| batched_auto_atomic_bs10 x200 | 1000 | 20 | 4000 | 1000 | 20 |
| batched_auto_atomic_bs50 x200 | 1000 | 4 | 4000 | 1000 | 4 |

---

## Scenario 7: Observer Overhead

### Timing

| Scenario | N ops | Wall (s) | Per-op (ms) | ops/s |
|----------|-------|----------|-------------|-------|
| with_observer x200 | 200 | 0.1653 | 0.826 | 1,210 |
| without_observer x200 | 200 | 0.1230 | 0.615 | 1,627 |
| raw_dv_with_observer x200 | 200 | 0.1908 | 0.954 | 1,048 |
| raw_dv_without_observer x200 | 200 | 0.0775 | 0.388 | 2,579 |

### Counters

| Scenario | observer.notify | pv.create_container | rocksdb.commit | rocksdb.get | rocksdb.put | storage.begin_transaction |
|----------|---:|---:|---:|---:|---:|---:|
| with_observer x200 | 1001 | 1000 | 200 | 4004 | 1004 | 200 |
| without_observer x200 | 0 | 1000 | 200 | 4004 | 1004 | 200 |
| raw_dv_with_observer x200 | 1002 | 1000 | 200 | 4005 | 1006 | 200 |
| raw_dv_without_observer x200 | 0 | 1000 | 200 | 4005 | 1006 | 200 |

---

## Key Observations

- **Raw TKV RocksDB (5 puts, 1 txn each):** 12,797 ops/sec (0.078ms/op)
- **Raw TKV RocksDB (5 puts, single txn):** 35,846 ops/sec (0.028ms/op)
- **Raw TKV RocksDB (5 gets):** 33,768 ops/sec (0.030ms/op)
- **auto_atomic per-term overhead:** 1.023ms/op (1000 txns/op)
- **Single Atomic:** 0.575ms/op (200 txns/op)
- **Raw DictView:** 0.305ms/op (200 txns/op)
- **Framework overhead vs raw:** 3.4x (auto_atomic), 1.9x (single Atomic)
- **Nesting depth cost:** depth-2 write = 0.326ms, depth-6 write = 0.335ms (1.0x)
- **Observer overhead:** with=0.826ms, without=0.615ms (delta=0.212ms)
