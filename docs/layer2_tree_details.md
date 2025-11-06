# Layer 2: Tree - Hierarchical Semantics

## Overview

The Tree layer interprets flat tuple-key-value storage as a hierarchical structure, providing parent-child relationships and distinguishing containers (nodes with children) from primitives (leaf values).

**Core Responsibility**: Add hierarchy semantics to flat storage - nothing more.

## Layer Position

```
┌─────────────────────────────────────────────┐
│ Layer 4: Semantics (Application Logic)     │
├─────────────────────────────────────────────┤
│ Layer 3: Views (Data Structures)           │
├─────────────────────────────────────────────┤
│ Layer 2: Tree (Hierarchical Semantics) ◄── │  THIS LAYER
├─────────────────────────────────────────────┤
│ Layer 1: Storage (Tuple-Key-Value)         │
└─────────────────────────────────────────────┘
```

## What Tree Does

✅ **Hierarchy Interpretation**
- Treats tuple keys as paths: `("users", "alice", "profile")`
- Parent-child relationships from key structure
- Root is empty tuple `()`

✅ **Type Distinction**
- Containers: Can have children (internal nodes)
- Primitives: Leaf values (terminal nodes)
- Type markers embedded in storage values

✅ **Rule Enforcement**
- Parent must exist before child
- Well-formed parent chain validation
- Type compatibility checking

✅ **Container Metadata**
- Structure ID: For View layer reconstruction
- Protocol flags: Hints for behavior (mutable/ordered/etc)

## What Tree Does NOT Do

❌ Data structure implementation (Views Layer 3)
❌ Application logic (Semantics Layer 4)
❌ Dict/list/queue semantics
❌ Protocol enforcement (protocols are hints only)

## Architecture

### Module Organization

```
redwood/tree/
├── __init__.py          # Public API exports
├── types.py             # Type definitions, enums, data structures
├── exceptions.py        # Exception hierarchy
├── marker.py            # Container type marker system
├── node.py              # Node identification
├── navigation.py        # Path operations (pure functions)
├── validation.py        # Rule enforcement
├── container.py         # Container CRUD and children
└── tree.py              # Main convenience interface
```

### Design Principles

**Functional Core**
- Most operations are pure functions taking explicit `ctx` parameter
- Stateless where possible (navigation is 100% pure)
- `Tree` class is optional convenience wrapper

**Immutable Data**
- All data structures frozen (thread-safe)
- Operations return new values
- No hidden state mutation

**Layered Validation**
- Information layer: Gather data without decisions
- Validation layer: Check conditions, raise errors
- Operation layer: Execute with proper validation

**Explicit Context**
- Transaction/snapshot passed explicitly
- Clear transaction boundaries
- No hidden storage access

## Container Type Markers

Containers are distinguished from primitives using special marker tuples embedded in storage values.

### Marker Structure

```python
# Format: (sentinel, structure_id, protocol_flags, sentinel)
marker = (
    "\ue000\U000f0000",          # Sentinel (PUA characters)
    ContainerStructure(1),        # Structure ID (int)
    ContainerProtocol.MUTABLE,    # Protocol flags (int)
    "\ue000\U000f0000"            # Sentinel (repeated)
)
```

### Sentinel Design

Uses Unicode Private Use Area characters from two planes:
- `U+E000`: BMP Private Use Area
- `U+F0000`: Supplementary Private Use Area A

This multi-plane combination provides strong collision resistance while remaining valid UTF-8.

### Structure IDs

Structure IDs are unbounded integers identifying container types for View reconstruction:

```python
ContainerStructure(1)  # Associative (dict-like)
ContainerStructure(2)  # Sequential (list-like)
ContainerStructure(3)  # Set
ContainerStructure(n)  # User-defined types
```

### Protocol Flags

Protocol flags are bitwise hints for debugging/visualization (NOT enforced):

```python
class ContainerProtocol(IntFlag):
    MUTABLE = 0x01   # Can be modified
    SIZED = 0x02     # Tracks child count
    INDEXED = 0x04   # Children are ordered
```

## Core Concepts

### Node Types

```python
class NodeType(Enum):
    CONTAINER = "container"  # Has children
    PRIMITIVE = "primitive"  # Leaf value
    NOT_FOUND = "not_found"  # Doesn't exist
```

### Paths and Hierarchy

Paths are tuples representing location in tree:

```python
()                          # Root
("users",)                  # Depth 1
("users", "alice")          # Depth 2
("users", "alice", "age")   # Depth 3
```

Parent-child relationships:
- `("users",)` is parent of `("users", "alice")`
- `("users", "alice")` is parent of `("users", "alice", "age")`
- Empty tuple `()` is root (no parent)

### Parent Chain

Every path has a parent chain from root to immediate parent:

```python
path = ("users", "alice", "profile")
chain = [
    (),                      # Root
    ("users",),              # Depth 1
    ("users", "alice")       # Depth 2 (immediate parent)
]
```

## API Overview

### Two API Styles

**Functional API** (recommended for libraries):
```python
from redwood.tree import create_container, get_node_info

with storage.transaction() as tx:
    create_container(
        ("users", "alice"),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx
    )
    info = get_node_info(("users", "alice"), tx)
```

**Object-Oriented API** (convenient for applications):
```python
from redwood.tree import Tree

with storage.transaction() as tx:
    tree = Tree(ctx=tx)
    tree.create_container(
        ("users", "alice"),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE
    )
    info = tree.get_node_info(("users", "alice"))
```

### Node Operations

```python
# Get complete node information
info = get_node_info(path, ctx)
info.exists       # bool
info.node_type    # NodeType
info.structure    # ContainerStructure | None
info.protocol     # ContainerProtocol | None

# Quick checks (hot paths)
exists = node_exists(path, ctx)
node_type = get_node_type(path, ctx)
```

### Navigation Operations

Pure functions (no storage access):

```python
parent = get_parent(("users", "alice"))          # ("users",)
ancestors = get_ancestors(("users", "alice"))    # [(), ("users",)]
chain = get_path_chain(("users", "alice"))       # [(), ("users",), ("users", "alice")]

is_ancestor(("users",), ("users", "alice"))      # True
get_depth(("users", "alice", "profile"))         # 3
```

### Validation Operations

```python
# Existence
validate_exists(path, ctx)      # Raises if missing
validate_not_exists(path, ctx)  # Raises if exists

# Type checking
validate_is_container(path, ctx)
validate_is_primitive(path, ctx)

# Parent chain
validate_parents_exist(path, ctx)    # All parents exist
validate_parents_healthy(path, ctx)  # All parents well-formed
validate_parents_chain(path, ctx)    # Both

# Type compatibility
validate_compatible(path, structure, protocol, ctx)

# Information gathering (no validation)
parent_info = gather_parent_info(path, ctx)
parent_info.all_exist    # bool
parent_info.all_healthy  # bool
```

### Container Operations

```python
# Lifecycle
created = create_container(path, structure, protocol, ctx, create_parents=True)
deleted = delete_container(path, ctx, recursive=True)
count = delete_subtree(path, ctx)

# Direct children (depth=1 only)
exists = has_child(path, "child_key", ctx)
child_type = get_child_type(path, "child_key", ctx)
keys = list_child_keys(path, ctx)
children = list_children(path, ctx)  # [(path, type), ...]
count = count_children(path, ctx)

# Child manipulation
create_child_container(parent, key, structure, protocol, ctx)
set_child_primitive(parent, key, value, ctx)
delete_child(parent, key, ctx, recursive=True)
clear_children(path, ctx)

# Recursive operations
descendants = list_descendants(path, ctx, max_depth=None)
for child_path, node_type in walk_tree(path, ctx):
    process(child_path, node_type)

# Parent management
created_paths = create_parents(path, structure, protocol, ctx)
created_paths = ensure_parents(path, structure, protocol, ctx)
```

## Usage Examples

### Basic Container Creation

```python
from redwood.tree import Tree, ContainerStructure, ContainerProtocol

with storage.transaction() as tx:
    tree = Tree(ctx=tx)

    # Create root container
    tree.create_container(
        ("users",),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE
    )

    # Create nested container (auto-creates parents)
    tree.create_container(
        ("users", "alice", "posts"),
        ContainerStructure(2),
        ContainerProtocol.MUTABLE | ContainerProtocol.INDEXED
    )
```

### Working with Children

```python
with storage.transaction() as tx:
    tree = Tree(ctx=tx)

    # Add primitive children
    tree.set_child_primitive(("users", "alice"), "name", "Alice")
    tree.set_child_primitive(("users", "alice"), "age", 30)

    # Add container child
    tree.create_child_container(
        ("users", "alice"),
        "settings",
        ContainerStructure(1),
        ContainerProtocol.MUTABLE
    )

    # List children
    for key in tree.list_child_keys(("users", "alice")):
        child_type = tree.get_child_type(("users", "alice"), key)
        print(f"{key}: {child_type}")
```

### Parent Chain Validation

```python
with storage.transaction() as tx:
    tree = Tree(ctx=tx)

    # Check parent chain health
    parent_info = tree.gather_parent_info(("users", "alice", "posts"))

    if not parent_info.all_exist:
        print(f"Missing parents: {parent_info.missing_paths}")
        # Create missing parents
        tree.create_parents(
            ("users", "alice", "posts"),
            ContainerStructure(1),
            ContainerProtocol.MUTABLE
        )

    if not parent_info.all_healthy:
        print(f"Malformed parents: {parent_info.malformed_paths}")
        # Manual intervention required
```

### Tree Traversal

```python
with storage.transaction() as tx:
    tree = Tree(ctx=tx)

    # Walk entire subtree
    for path, node_type in tree.walk_tree(("users",)):
        if node_type == NodeType.CONTAINER:
            child_count = tree.count_children(path)
            print(f"Container {path}: {child_count} children")
        else:
            print(f"Primitive {path}")

    # List descendants at specific depth
    level2 = tree.list_descendants(("users",), max_depth=2)
```

## Error Handling

```python
from redwood.tree import (
    PathNotFoundError,
    PathExistsError,
    PathTypeError,
    ParentNotFoundError
)

try:
    tree.create_container(path, structure, protocol)
except PathExistsError:
    # Container already exists with incompatible type
    pass
except ParentNotFoundError:
    # Parent chain incomplete
    tree.ensure_parents(path)
    tree.create_container(path, structure, protocol)
except PathTypeError:
    # Type mismatch or malformed data
    pass
```

## Performance Characteristics

**Hot Paths** (optimized):
- `node_exists()`: Single storage read
- `get_node_type()`: Single storage read + fast marker check
- Navigation functions: Pure computation (no I/O)

**Cold Paths**:
- `get_node_info()`: Single storage read + marker parsing
- `list_child_keys()`: Range scan at target depth
- `walk_tree()`: Full subtree scan (generator)

**Complexity**:
- Parent chain: O(depth)
- Direct children: O(children)
- Descendants: O(descendants)
- Navigation: O(depth) or O(1)

## Integration with Storage Layer

Tree operations translate to storage operations:

```python
# Tree operation
create_container(("users", "alice"), structure, protocol, ctx)

# Storage operation
ctx.set(
    ("users", "alice"),
    ("\ue000\U000f0000", structure, protocol, "\ue000\U000f0000")
)

# Tree operation
list_child_keys(("users",), ctx)

# Storage operation
ctx.scan(ScanOptions(
    start=("users", ""),
    end=("users", "\uffff")
))
```

## Testing Strategy

**Unit Tests**: Per module
- types.py: Enum values, data structure creation
- marker.py: Marker creation/extraction, collision resistance
- node.py: Node type detection, info gathering
- navigation.py: Pure path operations
- validation.py: Rule enforcement
- container.py: CRUD operations

**Integration Tests**: Cross-module
- Parent chain validation + creation
- Container creation with auto-parent creation
- Tree traversal with mixed nodes

**Property Tests**: Invariants
- Parent always has lower depth than child
- Marker round-trip (create → extract → create)
- Path operations are consistent

## Migration from Old Implementation

The new tree module replaces the monolithic `ContainerNode` class:

**Old API**:
```python
container = ContainerNode.create(
    backend=backend,
    ctx=tx,
    path=path,
    structure=structure,
    protocol=protocol
)
container.ensure_exists()
```

**New API**:
```python
create_container(path, structure, protocol, tx, create_parents=True)
# or
tree = Tree(ctx=tx)
tree.create_container(path, structure, protocol)
```

Benefits:
- Explicit context passing
- Functional API for testing
- Modular design (< 500 lines per file)
- Clear separation of concerns
