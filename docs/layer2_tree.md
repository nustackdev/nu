# Layer 2: Tree

## What It Is

Tree adds hierarchical semantics on top of flat TKV storage. It interprets tuple keys as paths and introduces the concept of containers.

## Key Concepts

### Tuples as Paths

TKV Storage sees: `("users", "alice")` as just a key
Tree sees: `("users", "alice")` as a path where `("users",)` is parent of `("users", "alice")`

### Containers vs Values

**Container**: A key that can have children

```python
("users",) → <CONTAINER_SENTINEL + metadata>
```

**Value**: A key that holds actual data (leaf)

```python
("users", "alice", "age") → 30
```

A key is either a container OR a value, not both.

### Container Sentinel

Containers are marked by storing a special sentinel value:

```python
{
    "type": "container",
    "structure_id": 12345,  # For View reconstruction
    "metadata": {...}
}
```

### Tree Rules

1. **Parent must exist before children**
   - Can't create `("users", "alice")` unless `("users",)` exists

2. **Can't replace type without explicit delete**
   - If `("users", "alice")` is a container, can't put a value there
   - Must delete first, then create

3. **Root always exists**
   - `()` (empty tuple) is the root container
   - Created automatically on storage initialization

## Operations

### Container Operations

```python
# Create container (validates parent exists)
tree.create_container(("users",))

# Check if key is a container
is_container = tree.is_container(("users",))

# Check if container has children
has_children = tree.has_children(("users",))

# Delete container and all descendants
tree.delete_subtree(("users", "alice"))
```

### Child Operations

```python
# List direct children
children = tree.list_children(("users",))
# Returns: [("users", "alice"), ("users", "bob")]

# List all descendants (recursive)
descendants = tree.list_descendants(("users",))
# Returns: [("users", "alice"), ("users", "alice", "profile"), ("users", "bob")]

# Count children
count = tree.count_children(("users",))
```

### Value Operations

```python
# Set value at path (parent must exist)
tree.set_value(("users", "alice", "age"), 30)

# Get value
value = tree.get_value(("users", "alice", "age"))

# Delete value
tree.delete_value(("users", "alice", "age"))
```

### Navigation

```python
# Get parent
parent = tree.get_parent(("users", "alice"))  # Returns: ("users",)

# Get children keys
keys = tree.child_keys(("users",))  # Returns: ["alice", "bob"]

# Check if path exists
exists = tree.exists(("users", "alice"))
```

## How It Uses Layer 1

Tree operations map to TKV Storage operations:

### list_children()

```python
# Tree Layer 2
children = tree.list_children(("users",))

# ↓ maps to TKV Layer 1
results = []
for key, value in tx.scan(start=("users",), end=("users", "￿")):
    if len(key) == len(("users",)) + 1:  # Direct children only
        results.append(key)
```

### delete_subtree()

```python
# Tree Layer 2
tree.delete_subtree(("users", "alice"))

# ↓ maps to TKV Layer 1
# Delete all keys in range [("users", "alice"), ("users", "alice", "￿"))
keys_to_delete = []
tx.rangeDelete(start=("users", "alice"))
```

### create_container()

```python
# Tree Layer 2
tree.create_container(("users", "alice"))

# ↓ maps to TKV Layer 1
# 1. Check parent exists
if not tx.exists(("users",)):
    raise ParentNotFoundError()

# 2. Check not already exists
if tx.exists(("users", "alice")):
    raise AlreadyExistsError()

# 3. Store sentinel
tx.put(("users", "alice"), sentinel)
```

## Structure Tracking

Containers store structure IDs for View layer reconstruction.

```python
# When creating a DictView
tree.create_container(("users",), structure_id=DictView.structure_id)

# When reading back
container = tree.get_container(("users",))
structure_id = container["structure_id"]
view_class = registry.get_view(structure_id)  # Returns: DictView
```

This allows Views to recreate themselves from storage.

## Validation

Tree enforces rules that TKV Storage doesn't:

### Parent Existence

```python
# TKV Storage: allows this
tx.put(("a", "b", "c"), "value")  # No parent check

# Tree: creates parents or raises
tree.set_value(("a", "b", "c"), "value")
```

### Type Consistency

```python
# TKV Storage: allows this
tx.put(("users", "alice"), <CONTAINER_SENTINEL>)
tx.put(("users", "alice"), "some value")  # Overwrites

# Tree: rejects this
tree.create_container(("users", "alice"))
tree.set_value(("users", "alice"), "value")  # Raises: AlreadyExistsError
```

## Isolation

Tree operations use TKV transactions:

```python
# All Tree operations happen in a transaction
with storage.begin(write=True) as tx:
    tree = Tree(tx)
    tree.create_container(("users",))
    tree.create_container(("users", "alice"))
    tree.set_value(("users", "alice", "age"), 30)
    # Auto-commits on exit
```

Multiple Tree operations in one transaction are atomic.

## What Tree Does NOT Do

### No Data Structure Semantics

Doesn't know:

- That `("users",)` should behave like a dict
- That `("tasks",)` should behave like a list
- How to append, pop, or other structure-specific operations

These are Layer 3 (Views) responsibilities.

### No Application Logic

Doesn't know:

- What "users" means
- Business rules or validation
- Domain models

These are Layer 4 (Semantics) responsibilities.

### No Query Language

Doesn't provide:

- "Find all users over age 30"
- Filters, sorting, aggregation
- Complex queries

Build these on top using Tree's iteration primitives.

## Usage Example

```python
from redwood.storage import create_lmdb_storage
from redwood.tree import Tree

# Create storage and tree
storage = create_lmdb_storage("data.db")

with storage.begin(write=True) as tx:
    tree = Tree(tx)

    # Create containers
    tree.create_container(("users",))
    tree.create_container(("users", "alice"))

    # Set values
    tree.set_value(("users", "alice", "name"), "Alice")
    tree.set_value(("users", "alice", "age"), 30)

    # Create another user
    tree.create_container(("users", "bob"))
    tree.set_value(("users", "bob", "name"), "Bob")

with storage.begin() as tx:
    tree = Tree(tx)

    # List users
    users = tree.list_children(("users",))
    print(users)  # [("users", "alice"), ("users", "bob")]

    # Get user data
    name = tree.get_value(("users", "alice", "name"))
    age = tree.get_value(("users", "alice", "age"))
    print(f"{name}, {age}")  # Alice, 30

    # Delete user and all their data
    tree.delete_subtree(("users", "alice"))
```
