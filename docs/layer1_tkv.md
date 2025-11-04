
# Layer 1: TKV Storage

## What It Is

A generic key-value store where keys are tuples instead of strings.

```python
# Traditional KV store
db["user:alice:name"] = "Alice"

# TKV store
db[("user", "alice", "name")] = "Alice"
```

## Key Properties

### Tuple Keys

Keys are tuples of components: `("users", "alice", "profile")`

- Components can be strings, ints, bytes, etc.
- Tuples are immutable and hashable

### Lexicographic Ordering

Keys are ordered like words in a dictionary:

```python
("a",) < ("a", "b") < ("a", "b", "c") < ("a", "c") < ("b",)
```

This ordering enables efficient range queries.

### Flat Storage

All keys are equal. No concept of hierarchy:

- `("users",)` and `("users", "alice")` are just two keys
- No relationship between them at this layer
- No concept of "parent", "child", "container", "value"

### Backend Agnostic

Works with any ordered KV store:

- LMDB (B-tree)
- RocksDB (LSM-tree)
- In-memory sorted dict
- SQLite with compound keys

## Operations

### 1. Point Access (single key)

```python
value = tx.get(key)                    # Read
tx.put(key, value)                     # Write
deleted = tx.delete(key)               # Delete
exists = tx.exists(key)                # Check
```

### 2. Scan Access (range iteration)

```python
# Scan all keys in range [start, end)
for key, value in tx.scan(
    start=("users", "a"),
    end=("users", "z"),
    reverse=False,
    limit=100,
):
    print(key, value)
```

The scan operation:

- Leverages lexicographic ordering
- Efficient: backend seeks to start position
- No concept of "prefix" or "children" - just range [start, end)

### 3. Batch Access (multiple keys)

```python
# Read multiple keys efficiently
results = tx.multiget([key1, key2, key3])

# Write multiple keys
tx.multiput({key1: val1, key2: val2})

# Delete multiple keys
tx.multidelete([key1, key2, key3])
```

### 4. Transactions (orthogonal)

```python
# Read-only snapshot
with storage.begin() as tx:
    value = tx.get(key)

# Read-write transaction
with storage.begin(write=True) as tx:
    tx.put(key, value)
    tx.commit()  # or tx.abort()
```

Transactions provide:

- Snapshot isolation
- ACID guarantees
- Automatic commit/abort on context exit

## Why Tuples?

### Efficient Prefix Queries

Want all keys starting with `("users",)`?

```python
# Traditional KV: scan everything, filter in memory
for key in db.all_keys():
    if key.startswith("users:"):
        yield key

# TKV: efficient range scan
for key, value in tx.scan(
    start=("users",),
    end=("users", "￿"),  # "￿" is max unicode char
):
    yield key
```

Backend can seek directly to `("users",)` and iterate until `("users", "￿")`.

### Natural Hierarchical Encoding

Tuples naturally represent paths:

```python
("users", "alice", "profile")
```

But TKV Storage doesn't KNOW this is hierarchical. Higher layers interpret it.

### Type Safety

```python
# Traditional KV: all strings, easy to make mistakes
db["user:alice:age"] = "30"  # Should be int?

# TKV: tuples preserve types
db[("users", "alice", "age")] = 30  # Clear
```

## What TKV Storage Does NOT Do

### No Hierarchy

Doesn't know:

- That `("users",)` is "parent" of `("users", "alice")`
- That certain keys are "containers"
- That parent should exist before children

These are Layer 2 (Tree) concepts.

### No Validation

Doesn't check:

- Parent exists before creating child
- Key types are consistent
- Structure is valid

These are Layer 2 responsibilities.

### No Semantics

Doesn't know:

- What values mean
- What a "DictView" or "ListView" is
- Application logic

These are Layer 3+ responsibilities.

## Implementation Notes

### Encoding

TKV keys must be encoded to backend format:

```python
tuple → bytes (eg for LMDB)
```

Encoding must preserve lexicographic order:

```python
encode(("a",)) < encode(("a", "b"))  # Must be true
```

Custom ecnoder used: rwtup (src /src/rwtup).

### Backend Requirements

Backend must provide:

- Ordered key-value storage
- Range iteration (seek to position, iterate forward/backward)
- Transactions (snapshot isolation)

Most modern KV stores provide this (LMDB, RocksDB, etc).

### Performance Characteristics

- Point access: O(log N) - tree lookup
- Range scan: O(log N + M) - seek + iterate M results
- Batch operations: O(K log N) - K individual operations, possibly pipelined

Where N = total keys, M = results, K = batch size.
