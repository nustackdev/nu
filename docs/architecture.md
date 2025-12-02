# EveryShape Architecture

## Overview

EveryShape is a layered data system. Each layer builds on the one below, adding one concept at a time.

```text
┌─────────────────────────────────────┐
│ Layer 4: Shapes                     │  Application logic, commands, queries
├─────────────────────────────────────┤
│ Layer 3: Views                      │  Data structures (Dict, List, Queue)
├─────────────────────────────────────┤
│ Layer 2: Tree                       │  Hierarchical semantics, containers
├─────────────────────────────────────┤
│ Layer 1:                            │  Flat tuple key-value store
│ + KV Storage Interface              │
│ + Backend: LMDB/RocksDB/etc>        │
└─────────────────────────────────────┘
```

## The Layers

### Layer 1: KV Storage

- Generic key-value store where keys are tuples
- No hierarchy, no semantics
- Provides: point access, range scans, transactions
- Example: `get(("users", "alice"))` returns a value, no concept of "parent" or "child"

### Layer 2: Tree

- Interprets tuples as hierarchical paths
- Introduces containers (can have children) vs primtivies (leaves)
- Enforces rules: parent must exist before children
- Example: `("users",)` is a container, `("users", "alice")` is its child

### Layer 3: Views

- Data structure abstractions built on Tree
- DictView, ListView, QueueView, etc.
- Auto-population and extraction of Python objects
- Example: `users["alice"] = {"name": "Alice"}` stores as tree structure

### Layer 4: Shapes

- Application logic and domain models
- Commands (mutations), queries (reads), refs (locations)
- Built on Views
- Example: `Market.orders["AAPL"].price.get()`

## Key Design Principles

### Separation of Concerns

Each layer knows ONLY its own concept:

- KV Storage: doesn't know what "container" means
- Tree: doesn't know what "DictView" means
- Views: don't know about application semantics
- Shapes: doesn't know about storage internals

### One Concept Per Layer

- Layer 1 adds: tuple keys + ordering
- Layer 2 adds: hierarchy + containers
- Layer 3 adds: data structures
- Layer 4 adds: domain logic

### Bottom-Up Composition

Higher layers use lower layer primitives:

- Tree uses KV's `scan()` to implement `list_children()`
- DictView uses Tree's containers to implement dict operations
- Shapes uses Views to implement domain objects

## Data Flow Example

Storing a user:

```python
# Layer 4 (Shapes)
users.alice.set({"name": "Alice", "age": 30})

# ↓ uses Layer 3 (View)
DictView.set("alice", {...})

# ↓ uses Layer 2 (Tree)
container.create_child_container("alice")
container.set_child_value("name", "Alice")
container.set_child_value("age", 30)

# ↓ uses Layer 1 (KV Storage)
tx.put(("users", "alice"), <CONTAINER_SENTINEL>)
tx.put(("users", "alice", "name"), "Alice")
tx.put(("users", "alice", "age"), 30)

# ↓ uses Backend
lmdb.put(encode(("users", "alice")), encode(<SENTINEL>))
lmdb.put(encode(("users", "alice", "name")), encode("Alice"))
lmdb.put(encode(("users", "alice", "age")), encode(30))
```

Reading a user:

```python
# Layer 4 (Shapes)
data = users.alice.get()

# ↓ uses Layer 3 (View)
DictView.extract()

# ↓ uses Layer 2 (Tree)
container.list_children()

# ↓ uses Layer 1 (KV Storage)
scan = tx.scan(ScanOptions(start=("users", "alice"), end=("users", "alice", "￿")))
for _ in scan.items():
    pass

# ↓ uses Backend
lmdb.iterator(encode(("users", "alice")), encode(("users", "alice", "￿")))
```

## Why This Architecture?

**Flexibility**: Each layer can be replaced independently

- Swap LMDB for RocksDB (Backend)
- Add new View types (Layer 3)
- Change domain models (Layer 4)

**Testability**: Each layer has clear boundaries

- Test KV Storage without Tree logic
- Test Tree without View logic
- Test Views without Shapes

**Performance**: Lower layers are optimized

- KV Storage maps directly to backend primitives
- No unnecessary abstractions
- Each layer adds minimal overhead

**Simplicity**: Each layer is simple in isolation

- KV Storage: just a KV store with tuple keys
- Tree: just adds container concept
- Views: just data structure patterns
- Shapes: just domain logic
