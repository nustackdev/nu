# Everybase Point Benchmark Results

**Date:** 2026-02-21 13:02:18
**Total runtime:** 5.5s
**Python:** 3.12.2

---

## Flat Writes

### Timing

| Scenario | N ops | Wall (s) | Per-op (ms) | ops/s |
|----------|-------|----------|-------------|-------|
| single_field x100 | 100 | 0.0160 | 0.160 | 6,241 |
| 10_fields_separate_atomic x100 | 100 | 0.3390 | 3.390 | 295 |
| 10_fields_single_atomic x100 | 100 | 0.0808 | 0.808 | 1,238 |
| 10_fields_auto_atomic x100 | 100 | 0.1228 | 1.228 | 814 |

### Counters

| Scenario | pv.create_container | rocksdb.commit | rocksdb.get | rocksdb.put | storage.begin_transaction |
|----------|---:|---:|---:|---:|---:|
| single_field x100 | 100 | 100 | 200 | 100 | 100 |
| 10_fields_separate_atomic x100 | 1000 | 1000 | 2009 | 1009 | 1000 |
| 10_fields_single_atomic x100 | 1000 | 100 | 2000 | 1000 | 100 |
| 10_fields_auto_atomic x100 | 1000 | 1000 | 2000 | 1000 | 1000 |

---

## Nested Shape Navigation

### Timing

| Scenario | N ops | Wall (s) | Per-op (ms) | ops/s |
|----------|-------|----------|-------------|-------|
| depth_2_write x100 | 100 | 0.0179 | 0.179 | 5,600 |
| depth_4_write x100 | 100 | 0.0210 | 0.210 | 4,752 |
| depth_6_write x100 | 100 | 0.0245 | 0.245 | 4,075 |
| depth_2_read x100 | 100 | 0.0072 | 0.072 | 13,974 |
| depth_4_read x100 | 100 | 0.0098 | 0.098 | 10,157 |
| depth_6_read x100 | 100 | 0.0144 | 0.144 | 6,951 |

### Counters

| Scenario | pv.create_container | pv.get_node_info | rocksdb.commit | rocksdb.get | rocksdb.put | storage.begin_snapshot | storage.begin_transaction |
|----------|---:|---:|---:|---:|---:|---:|---:|
| depth_2_write x100 | 100 | 0 | 100 | 200 | 100 | 0 | 100 |
| depth_4_write x100 | 100 | 0 | 100 | 200 | 100 | 0 | 100 |
| depth_6_write x100 | 100 | 0 | 100 | 200 | 100 | 0 | 100 |
| depth_2_read x100 | 0 | 100 | 0 | 100 | 0 | 100 | 0 |
| depth_4_read x100 | 0 | 100 | 0 | 100 | 0 | 100 | 0 |
| depth_6_read x100 | 0 | 100 | 0 | 100 | 0 | 100 | 0 |

---

## Dict-of-Shapes CRUD

### Timing

| Scenario | N ops | Wall (s) | Per-op (ms) | ops/s |
|----------|-------|----------|-------------|-------|
| create_10_entries | 10 | 0.0040 | 0.400 | 2,501 |
| create_10_entries_batched | 10 | 0.0050 | 0.505 | 1,981 |
| read_10_entries_fields | 10 | 0.0024 | 0.238 | 4,194 |
| update_10_entries_1field | 10 | 0.0019 | 0.190 | 5,262 |
| create_100_entries | 100 | 0.0330 | 0.330 | 3,033 |
| create_100_entries_batched | 100 | 0.0338 | 0.338 | 2,958 |
| read_100_entries_fields | 100 | 0.0185 | 0.185 | 5,407 |
| update_100_entries_1field | 100 | 0.0141 | 0.141 | 7,089 |
| create_500_entries | 500 | 0.1651 | 0.330 | 3,028 |
| create_500_entries_batched | 500 | 0.1530 | 0.306 | 3,268 |
| read_500_entries_fields | 500 | 0.1040 | 0.208 | 4,807 |
| update_500_entries_1field | 500 | 0.0704 | 0.141 | 7,107 |

### Counters

| Scenario | pv.create_container | pv.get_node_info | rocksdb.commit | rocksdb.get | rocksdb.put | rocksdb.scan | storage.begin_snapshot | storage.begin_transaction |
|----------|---:|---:|---:|---:|---:|---:|---:|---:|
| create_10_entries | 40 | 22 | 10 | 72 | 52 | 0 | 0 | 10 |
| create_10_entries_batched | 50 | 0 | 1 | 130 | 50 | 10 | 0 | 1 |
| read_10_entries_fields | 0 | 30 | 0 | 30 | 0 | 0 | 10 | 0 |
| update_10_entries_1field | 10 | 0 | 10 | 20 | 10 | 0 | 0 | 10 |
| create_100_entries | 400 | 202 | 100 | 702 | 502 | 0 | 0 | 100 |
| create_100_entries_batched | 500 | 0 | 1 | 1300 | 500 | 100 | 0 | 1 |
| read_100_entries_fields | 0 | 300 | 0 | 300 | 0 | 0 | 100 | 0 |
| update_100_entries_1field | 100 | 0 | 100 | 200 | 100 | 0 | 0 | 100 |
| create_500_entries | 2000 | 1002 | 500 | 3502 | 2502 | 0 | 0 | 500 |
| create_500_entries_batched | 2500 | 0 | 1 | 6500 | 2500 | 500 | 0 | 1 |
| read_500_entries_fields | 0 | 1500 | 0 | 1500 | 0 | 0 | 500 | 0 |
| update_500_entries_1field | 500 | 0 | 500 | 1000 | 500 | 0 | 0 | 500 |

---

## List Ops

### Timing

| Scenario | N ops | Wall (s) | Per-op (ms) | ops/s |
|----------|-------|----------|-------------|-------|
| store_list_int_10 | 1 | 0.0008 | 0.817 | 1,224 |
| store_list_str_10 | 1 | 0.0005 | 0.549 | 1,821 |
| read_list_int_10 | 1 | 0.0003 | 0.285 | 3,507 |
| read_by_index_10 | 10 | 0.0009 | 0.089 | 11,200 |
| append_one_by_one_10 | 10 | 0.0029 | 0.291 | 3,438 |
| store_list_int_100 | 1 | 0.0033 | 3.290 | 304 |
| store_list_str_100 | 1 | 0.0034 | 3.361 | 298 |
| read_list_int_100 | 1 | 0.0008 | 0.793 | 1,261 |
| read_by_index_100 | 100 | 0.0100 | 0.100 | 10,045 |
| append_one_by_one_100 | 100 | 0.0610 | 0.610 | 1,640 |
| store_list_int_500 | 1 | 0.0114 | 11.389 | 88 |
| store_list_str_500 | 1 | 0.0110 | 11.046 | 91 |
| read_list_int_500 | 1 | 0.0033 | 3.281 | 305 |
| read_by_index_500 | 500 | 0.0308 | 0.062 | 16,243 |
| append_one_by_one_500 | 500 | 0.8221 | 1.644 | 608 |

### Counters

| Scenario | pv.create_container | pv.get_node_info | rocksdb.commit | rocksdb.get | rocksdb.put | rocksdb.scan | storage.begin_snapshot | storage.begin_transaction |
|----------|---:|---:|---:|---:|---:|---:|---:|---:|
| store_list_int_10 | 11 | 2 | 1 | 14 | 14 | 1 | 0 | 1 |
| store_list_str_10 | 11 | 1 | 1 | 13 | 13 | 1 | 0 | 1 |
| read_list_int_10 | 0 | 0 | 0 | 1 | 0 | 1 | 1 | 0 |
| read_by_index_10 | 0 | 10 | 0 | 20 | 0 | 0 | 10 | 0 |
| append_one_by_one_10 | 10 | 0 | 10 | 30 | 20 | 10 | 0 | 10 |
| store_list_int_100 | 101 | 2 | 1 | 104 | 104 | 1 | 0 | 1 |
| store_list_str_100 | 101 | 1 | 1 | 103 | 103 | 1 | 0 | 1 |
| read_list_int_100 | 0 | 0 | 0 | 1 | 0 | 1 | 1 | 0 |
| read_by_index_100 | 0 | 100 | 0 | 200 | 0 | 0 | 100 | 0 |
| append_one_by_one_100 | 100 | 0 | 100 | 300 | 200 | 100 | 0 | 100 |
| store_list_int_500 | 501 | 2 | 1 | 504 | 504 | 1 | 0 | 1 |
| store_list_str_500 | 501 | 1 | 1 | 503 | 503 | 1 | 0 | 1 |
| read_list_int_500 | 0 | 0 | 0 | 1 | 0 | 1 | 1 | 0 |
| read_by_index_500 | 0 | 500 | 0 | 1000 | 0 | 0 | 500 | 0 |
| append_one_by_one_500 | 500 | 0 | 500 | 1500 | 1000 | 500 | 0 | 500 |

---

## Atomic Granularity

### Timing

| Scenario | N ops | Wall (s) | Per-op (ms) | ops/s |
|----------|-------|----------|-------------|-------|
| auto_atomic_per_term x200 | 200 | 0.1429 | 0.714 | 1,400 |
| single_atomic x200 | 200 | 0.0764 | 0.382 | 2,619 |
| batched_atomic_bs10 x200 | 200 | 0.0377 | 0.188 | 5,312 |
| batched_atomic_bs50 x200 | 200 | 0.0291 | 0.145 | 6,879 |

### Counters

| Scenario | pv.create_container | rocksdb.commit | rocksdb.get | rocksdb.put | storage.begin_transaction |
|----------|---:|---:|---:|---:|---:|
| auto_atomic_per_term x200 | 1000 | 1000 | 2000 | 1000 | 1000 |
| single_atomic x200 | 1000 | 200 | 2000 | 1000 | 200 |
| batched_atomic_bs10 x200 | 1000 | 20 | 2000 | 1000 | 20 |
| batched_atomic_bs50 x200 | 1000 | 4 | 2000 | 1000 | 4 |

---

## Key Observations

- **auto_atomic per-term:** 0.714ms/op (1000 txns)
- **Single Atomic:** 0.382ms/op (200 txns)
- **Nesting depth cost:** depth-2 write = 0.179ms, depth-6 write = 0.245ms (1.4x)
