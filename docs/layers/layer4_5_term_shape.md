# Layer 4, 5: Terms + Shapes

## Overview

The Terms system turns declarative structure into executable meaning.
It provides application-level abstractions where developers describe *what exists* (Shapes), *where it lives* (Slots),
and *how to interact with it* (Terms: Refs, Operations, Commands).

**Core Responsibility**: Provide type-safe, declarative data structures with semantic operations.

## Layer Position


```text
┌─────────────────────────────────────┐
│ Layer 5: Shapes  <--- (this)        │  Models for term system (Market.symbols["AAPL"])
├─────────────────────────────────────┤
│ Layer 4: Terms   <--- (and this)    │  Declarative computation interface over data (Ref("symbols", "AAPL").get() + 12)
├─────────────────────────────────────┤
│ Layer 3: Views                      │  Data structures (Dict, List, Queue)
├─────────────────────────────────────┤
│ Layer 2: Container                  │  Hierarchical semantics, containers
├─────────────────────────────────────┤
│ Layer 1:                            │  Flat tuple key-value store
│ + KV Storage Interface              │
│ + Backend: LMDB/RocksDB/etc>        │
└─────────────────────────────────────┘
```

## What It Is

Terms and Shapes is a **cognitive model** for data:

Shapes:
- **Shape**: Blueprint defining structure
- **Slot**: Position within structure (field definition)

Terms:
- **Ref**: Runtime address pointing to data (LValue)
- **Operation**: Pure computation producing values (RValue)
- **Command**: Impure mutation changing state (RValue)

> *"Shapes define form. Slots define positions. Refs locate them. Operations read. Commands change."*

## Core Vocabulary

### Term Hierarchy

```text
Term                        - executable node
├── LValue                  - addressable location (has path)
│   └── Ref                 - typed reference to storage location
│       ├── ViewRef         - reference to container (dict, list, set)
│       └── PrimitiveRef    - reference to leaf value (int, str, etc.)
└── RValue                  - evaluable expression (has children)
    ├── Value               - represents a value (literal or computed)
    │   ├── LiteralValue    - fixed value (e.g. 42, "hello")
    │   └── ComputedValue   - result of computation (wraps Operation)
    └── Computation         - computes or mutates
        ├── Operation       - pure computation (e.g. get, add)
        └── Command         - impure mutation (e.g. set, delete)
```

### Shape - Declarative Structure

Shapes are class-level definitions describing data topology:

```python
from everyshape.semantics import Shape, ValueSlot, ShapeSlot, MapSlot

class Order(Shape):
    price = ValueSlot(float)
    volume = ValueSlot(int)
    filled = ValueSlot(bool)

class Market(Shape):
    signal = ValueSlot(float)
    orders = MapSlot(Order)
```

**Properties**:

- Never instantiated (class-level only)
- Declarative (no behavior, just structure)
- Composable (Shapes contain other Shapes)
- Type-safe (IDE autocomplete via descriptors)

### Slot - Position Definition

Slots are factory objects that create Refs when accessed:

| Slot Type | Creates | Purpose | Example |
|-----------|---------|---------|---------|
| `ValueSlot` | `ValueRef` | Primitive values | `price = ValueSlot(float)` |
| `ShapeSlot` | `ShapeRef` | Nested shapes | `profile = ShapeSlot(Profile)` |
| `MapSlot` | `MapRef` | Key→value mappings | `orders = MapSlot(Order)` |
| `ListSlot` | `ListRef` | Index→value sequences | `tags = ListSlot(str)` |

**Key Insight**: Slots are declarative factories. They don't hold data—they define how to create Refs to data.

### Ref - Runtime Address (LValue)

Refs are addressable locations in the data tree:

```python
# Static refs (path known at definition)
signal_ref = Market.signal                    # ValueRef to float
orders_ref = Market.orders                    # MapRef to Order mapping

# Dynamic refs (path determined at runtime)
order_ref = Market.orders["AAPL"]             # MapItemRef
price_ref = Market.orders["AAPL"].price       # ValueRef via ShapeRef
```

**Properties**:

- Addressable (resolve to tuple-key paths)
- Navigable (support nested access)
- Static or dynamic (path may require runtime evaluation)
- Type-carrying (know their value_type and view_type)

### Operation - Pure Computation (RValue)

Operations read and compute without side effects:

```python
# Read operations
price = Market.orders["AAPL"].price.get()     # GetOp

# Binary operations
expensive = price > 100                        # BinaryOp (CmpOp)
total = price * volume                         # BinaryOp (ArithOp)

# Unary operations
negative = -price                              # UnaryOp
```

**Guarantees**:

- No side effects
- Deterministic
- Cacheable
- Composable

### Command - Impure Mutation (RValue)

Commands change state with side effects:

```python
# Set values
Market.signal.set(42.0)                       # SetCmd

# Delete entries
Market.orders["AAPL"].delete()                # DeleteCmd

# Update via function
Market.orders["AAPL"].price.update(lambda p: p * 1.1)  # UpdateCmd
```

**Guarantees**:

- Side effects explicit
- Transactional
- Type-safe

## How It Uses Layer 3

Shapes builds on Views for data access:

### Reading: Ref → View → Value

```python
# Shapes Layer 4
price_value = Market.orders["AAPL"].price.get()

# ↓ resolves to path
path = ("orders", "AAPL", "price")

# ↓ uses View Layer 3
view = tree.at("orders").view(DictView)
order_view = view.get("AAPL")
price = order_view["price"]

# ↓ uses Tree Layer 2
value = tree.get_child_primitive(path)

# ↓ uses Storage Layer 1
storage.get(path)
```

### Writing: Cmd → View → Tree

```python
# Shapes Layer 4
Market.orders["AAPL"].price.set(150.0)

# ↓ resolves to path
path = ("orders", "AAPL", "price")

# ↓ uses View Layer 3
view = tree.at("orders").view(DictView)
order_view = view.get("AAPL")
order_view["price"] = 150.0

# ↓ uses Tree Layer 2
tree.set_child_primitive(path, 150.0)

# ↓ uses Storage Layer 1
storage.put(path, 150.0)
```

### Nested Structures: Auto-Population

```python
# Single write with nested structure
Market.orders.set({
    "AAPL": {"price": 150.0, "volume": 100},
    "GOOGL": {"price": 2800.0, "volume": 50}
})

# ↓ View Layer 3 handles recursion
dict_view = tree.at("orders").view(DictView)
dict_view.store({...}, replace=True)

# ↓ Creates nested containers automatically
# Tree creates: orders/AAPL, orders/GOOGL
# Then stores: orders/AAPL/price, orders/AAPL/volume, etc.
```

## What It Does

✅ **Declarative Structure**

- Shape definitions with Slots
- Type-safe field access
- Nested composition

✅ **Runtime Navigation**

- Ref creation and resolution
- Static and dynamic path computation
- Nested field traversal

✅ **Semantic Operations**

- Pure reads (GetOp, BinaryOp, etc.)
- Impure mutations (SetCmd, DeleteCmd, etc.)
- Type-safe execution

✅ **Domain Modeling**

- Application-specific data structures
- Custom operations and commands
- Business logic encapsulation

## What It Does NOT Do

### No Direct Storage Access

Doesn't handle:

- Key-value operations
- Transactions
- Encoding/decoding

These are Storage Layer 1 responsibilities.

### No Hierarchy Management

Doesn't handle:

- Container creation rules
- Parent validation
- Type markers

These are Tree Layer 2 responsibilities.

### No Data Structure Patterns

Doesn't handle:

- Dict/list/set implementations
- Registry management
- Auto-population logic

These are View Layer 3 responsibilities.

## Summary

Layer 4, 5 provide the **cognitive model** for EveryShape:

- **Shapes** define structure declaratively
- **Slots** create Refs when accessed
- **Refs** address data locations
- **Operations** read and compute
- **Commands** write and mutate

This vocabulary gives developers a clear mental model: describe what exists, where it lives, and how to interact with it. The system handles the rest—navigation, storage, transactions, and type safety.

The semantics layer is where EveryShape transforms from a generic tree store into a domain-specific data platform.
