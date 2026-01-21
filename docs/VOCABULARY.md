# Vocabulary & Semantics

This document defines the core terminology and semantics of the every ecosystem.

---

## Core Concepts

### Term

**Definition:** The root abstraction. Everything in the system is a Term.

**Semantics:** A Term is a node in a computation graph that can be executed to produce a value.

**Properties:**
- `execute(ctx) → T | Sentinel` - evaluate this term

**Kinds:**

- **Ref** - denotes a location
- **Morphism** - denotes a transformation

```text
Term[T]
├── Ref[T]
└── Morphism[T]
```

---

### Ref

**Definition:** A reference to a location where a value lives.

**Semantics:** Refs are pointers, not values. They answer "where is it?" not "what is it?".

**Etymology:** Short for "reference" - a pointer to a location.

**Properties:**

- May or may not be **Gettable** (can extract value)
- May or may not be **Settable** (can mutate value)
- Executes by getting its value (if Gettable)

**Examples:**

```python
IntRef(42)              # Ref to Python memory location holding 42
KVIntRef("users/age")   # Ref to KV store location
NotionIntRef(cell)      # Ref to Notion cell location
```

**Not all Refs are equal:**

- Some refs are read-only (Gettable but not Settable)
- Some refs are write-only (Settable but not Gettable)
- Some refs are opaque (neither) - just location markers

---

### Morphism

**Definition:** A transformation that maps inputs to an output.

**Semantics:** Morphisms answer "how to compute?" They take operands and produce results.

**Etymology:** From category theory - a structure-preserving map between objects.

**Properties:**

- Has `children` - tuple of operands (Terms or literals)
- `execute(ctx)` - resolve operands, apply transformation
- `_apply(*values)` - the actual transformation logic

**Why "Morphism"?**

- More precise than "computation" or "operation"
- Evokes mathematical rigor
- Clearly distinct from "Ref"

---

### Arity

**Definition:** The number of operands a morphism takes.

**Kinds:**

| Arity | Class | Operands | Examples |
|-------|-------|----------|----------|
| 1 | `UnaryMorphism` | operand | `-x`, `abs(x)`, `not x` |
| 2 | `BinaryMorphism` | left, right | `x + y`, `x > y`, `x and y` |
| 3 | `TernaryMorphism` | a, b, c | `if a then b else c` |
| N | `NAryMorphism` | *operands | `sum(a, b, c, ...)` |

**`NAryMorphism`** is the base class providing:

- Operand resolution
- Sentinel propagation
- The `_apply()` contract

---

### Purity

**Definition:** Whether a morphism has side effects.

**Two kinds:**

| | Operation | Command |
|---|-----------|---------|
| **Side effects** | Maybe (depends on children) | Yes |
| **Deterministic** | Yes | Maybe |
| **Cacheable** | Yes | No |
| **Order matters** | No | Yes |

**Operation** (Pure):
```python
class AddOp(BinaryMorphism, Operation):
    # No side effects - just computes
    def _apply(self, left, right):
        return left + right
```

**Command** (Impure):
```python
class SetCmd(BinaryMorphism, Command):
    # Side effect - mutates storage
    def _apply(self, ref, value):
        ref.set(ctx, value)
        return value
```

**Orthogonality:** Purity is independent of arity. You can have:
- `UnaryMorphism + Operation` (e.g., `NegOp`)
- `UnaryMorphism + Command` (e.g., `DeleteCmd`)
- `BinaryMorphism + Operation` (e.g., `AddOp`)
- `BinaryMorphism + Command` (e.g., `SetCmd`)

---

### Sentinel

**Definition:** Special values representing absence or failure.

**Kinds:**

| Sentinel | Meaning | When |
|----------|---------|------|
| `Empty` | Location has no value | Key doesn't exist, field is null |
| `Invalid` | Operation cannot produce result | Type error, division by zero |
| `NotSet` | Parameter not provided | Distinct from `None` |

**Propagation:** Sentinels propagate through morphisms:
```python
Empty + 5     → Invalid
Invalid * 2   → Invalid
```

**Checking:**
```python
is_empty(value)     # True if Empty
is_invalid(value)   # True if Invalid
is_sentinel(value)  # True if any sentinel
```

---

### Gettable / Settable

**Definition:** Protocols for Ref capabilities.

**Gettable:**
```python
@runtime_checkable
class Gettable[T](Protocol):
    def get(self, ctx: Context) -> T | Sentinel: ...
```

**Settable:**
```python
@runtime_checkable
class Settable[T](Protocol):
    def set(self, ctx: Context, value: T) -> Self: ...
```

**Usage:**
```python
if isinstance(ref, Gettable):
    value = ref.get(ctx)

if isinstance(ref, Settable):
    ref.set(ctx, new_value)
```

**Not all Refs implement these.** They're capabilities, not requirements.

---

### Trait

**Definition:** Capability mixin providing operators/methods.

**Semantics:** Traits add behavior to Refs without specifying storage.

**Examples:**
```python
class Addable:
    def __add__(self, other) -> Ref: ...
    def __radd__(self, other) -> Ref: ...

class Orderable:
    def __lt__(self, other) -> BoolRef: ...
    def __gt__(self, other) -> BoolRef: ...
```

**Composition:**
```python
class IntRefBase(Numeric, Bitwise, Comparable, Ref[int], Gettable[int]):
    # Has all int operations from traits
    # Has get() from Gettable
    # Is a Ref pointing to int location
    ...
```

**Traits vs Protocols:**
- **Trait** = provides implementation (mixin)
- **Protocol** = defines interface (structural typing)

---

### Substrate

**Definition:** Where values physically live.

**Examples:**
| Substrate | Package | Description |
|-----------|---------|-------------|
| Python memory | `everybase.py` | Immediate values, computed results |
| KV store | `std/every_kv` | Key-value storage |
| Views | `std/every_pv` | Container layer |
| Notion | `pkgs/every_notion` | Notion API |
| Postgres | `pkgs/every_postgres` | PostgreSQL |

**Substrate-specific Refs:**
```python
IntRef          # Python memory
IntKVRef        # KV store
IntNotionRef    # Notion cell
```

**Protocol enforcement:** All operations return Python memory refs (`IntRef`, `BoolRef`, etc.), regardless of source substrate.

---

### Shape

**Definition:** Declarative structure definition.

**Semantics:** Shapes declare "what exists where" using Slots.

```python
class Order(Shape):
    price = ValueSlot(float)
    volume = ValueSlot(int)

class Market(Shape):
    orders = MapSlot(str, Order)
```

**Shapes are:**
- Declarative (describe structure, not behavior)
- Composable (shapes contain shapes)
- Substrate-agnostic (slots determine actual refs)

---

### Slot

**Definition:** Factory for creating Refs.

**Semantics:** Slots are placeholders that create appropriate Refs when accessed.

```python
class ValueSlot[T](Slot):
    def create_ref(self, owner, parent) -> Ref[T]: ...

class MapSlot[K, V](Slot):
    def create_ref(self, owner, parent) -> MapRef[K, V]: ...
```

**Access creates Refs:**
```python
Market.orders           # → MapRef
Market.orders["AAPL"]   # → OrderRef
Market.orders["AAPL"].price  # → FloatRef
```

---

### Context

**Definition:** Execution environment.

**Provides:**
- Storage access
- Transaction state
- Runtime configuration

```python
ctx = Context(storage=kv_store, transaction=tx)
value = ref.get(ctx)
morphism.execute(ctx)
```

---

## Hierarchy Summary

```
Term[T]                          # Everything is a Term
├── Ref[T]                       # Location ("where")
│   ├── Gettable                 # Can extract value
│   └── Settable                 # Can mutate value
│
└── Morphism[T]                  # Transformation ("what")
    └── NAryMorphism[T]          # With operand handling
        ├── UnaryMorphism[T]     # 1 operand
        ├── BinaryMorphism[T]    # 2 operands
        └── TernaryMorphism[T]   # 3 operands

# Orthogonal purity:
Operation                        # Pure (no side effects)
Command                          # Impure (has side effects)

# Composition example:
AddOp = BinaryMorphism + Operation
SetCmd = BinaryMorphism + Command
```

---

## Naming Conventions

| Concept | Naming | Examples |
|---------|--------|----------|
| Abstract ref | `*RefBase` | `IntRefBase`, `StrRefBase` |
| Concrete ref | `*Ref` | `IntRef`, `IntKVRef`, `IntNotionRef` |
| Pure morphism | `*Op` | `AddOp`, `EqOp`, `LenOp` |
| Impure morphism | `*Cmd` | `SetCmd`, `DeleteCmd` |
| Trait | Adjective | `Addable`, `Orderable`, `Gettable` |
| Compound trait | Noun | `Numeric`, `Comparable`, `Sequence` |

---

## Package Semantics

```
every       = Contracts    "what things ARE"
everybase   = Foundations  "how things WORK"
std/*       = Substrates   "where values LIVE" (standard)
pkgs/*      = Substrates   "where values LIVE" (external)
```
