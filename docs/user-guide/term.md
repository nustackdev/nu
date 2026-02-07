# Term

A Term is a computation node. It answers: **what** gets computed.

## Core Idea

Terms are lazy. Building `a.get() + b.get()` (just `a + b` also works) creates a tree with three nodes — it doesn't execute anything. The tree is data. Execution is a separate act.

```python
# This builds a tree, nothing executes yet
expr = User.age + 2  # or explicit: User.age.get() + 1

# This executes the tree against a context
result = await expr.execute(ctx)
```

## Hierarchy

```
Term[ResultT]                     executable node, produces a value
├── LValue[T]                     addressable location (can be read/written)
│   └── Ref[T]                    typed reference to storage
└── RValue[ResultT]               evaluable expression (no address)
    ├── Value[T]                  typed value holder
    └── Morphism[T]               transformation node
        ├── Operation             pure (deterministic, cacheable)
        └── Command               impure (order-dependent, stateful)
```

**LValue vs RValue:**

- LValue (Ref) has an address — `User.name` points to a storage location
- RValue (Value/Morphism) is pure computation — `User.age.get() + 1` has no address

**Operation vs Command:**

- Operation (`is_self_pure = True`): `AddOp`, `EqOp`, `LenOp` — safe to cache, reorder, parallelize
- Command (`is_self_pure = False`): `ItemSetCmd`, `DeleteCmd` — order matters, may need transactions

## Values

Values are typed containers for either literals or computation sources:

```python
from everybase.abc import IntValue, StrValue, FloatValue, BoolValue

# Literal values
x = IntValue(42)
s = StrValue("hello")

# Computed values (wrapping a morphism)
y = IntValue(AddOp(x, IntValue(1)))  # represents 42 + 1, not yet evaluated
```

## Morphisms

Morphisms are transformations. They resolve their children first, then apply:

```python
from everybase.abc import AddOp, FuncCallOp, MethodCallOp

# Arithmetic — binary operation
total = IntValue(AddOp(price, tax))

# Function call — wrap any Python function
dt = DatetimeValue(FuncCallOp(datetime.fromtimestamp, ts))

# Method call — call a method on a value
s = StrValue(MethodCallOp(name, "upper"))
```

The execute cycle for a morphism:

1. Resolve each child by calling `child.execute(ctx)`
2. If any child is a Sentinel (EMPTY/INVALID), return INVALID without calling apply
3. Call `apply(*resolved_values)` to produce the result

## Refs

Refs are LValues — they point to a location in storage. The substrate determines how they resolve:

```python
from eb_dict import IntRef, StrRef
from eb_shape import Shape

class Counter(Shape):
    value = IntRef.slot()
    label = StrRef.slot()

# Reading — returns a Value term (lazy)
expr = Counter.value.get()

# Writing — returns a Command term (lazy)
expr = Counter.value.set(10)

# Composing — builds a tree
expr = Counter.value.set(Counter.value.get() + 1)

# Executing — actually does the work
await expr.execute(ctx)
```

## Purity

Every Term knows if it's pure:

```python
term.is_self_pure       # this node only
term.is_subtree_pure    # this node + all descendants
```

This matters for Spans — a pure subtree can use a read-only snapshot instead of a full transaction.

## Example: Expression Tree

```python
from eb_dict import IntRef, StrRef
from eb_shape import Shape
from everybase import Context

class Wallet(Shape):
    balance = IntRef.slot()
    owner = StrRef.slot()

# Build context
data = {}
ctx = Context().with_handle(dict, data, shape=Wallet)

# Build expression tree (nothing executes)
deposit = Wallet.balance.set(Wallet.balance.get() + 100)

# Execute
await deposit.execute(ctx)
# data is now {"balance": <previous + 100>}
```

## Example: Combining Operations

```python
from everybase.abc import FuncCallOp, MethodCallOp, StrValue, IntValue

# Compute a formatted label from stored values
label = StrValue(FuncCallOp(
    str.format,
    "Wallet {} has {} SOL",
    Wallet.owner  # or with explicit .get(),
    Wallet.balance,
))

result = await label.execute(ctx)
# "Wallet Alice has 150 SOL"
```

## Node Contract

Every Term subclass **must** call `super().__init__()` with its children:

```python
# CORRECT
class MyOp(Operation, UnaryMorphism[int]):
    def __init__(self, operand):
        super().__init__(operand)

# WRONG — breaks tree traversal, purity detection, everything
class MyOp(Operation, UnaryMorphism[int]):
    def __init__(self, operand):
        self.operand = operand  # _children never set!
```
