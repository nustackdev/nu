# Getting Started with everybase

This guide walks you through every concept in everybase, from zero to building real applications. Each section builds on the previous one — follow it top to bottom.

---

## What is everybase?

everybase lets you build applications as **declarative trees** instead of imperative scripts.

Instead of writing Python control flow and calling storage APIs directly, you describe *what* should happen, *when* it should run, and *which* resources it needs. everybase composes these descriptions into a tree, then executes it.

```python
# Traditional Python
user = db.get("alice")
user["age"] = user["age"] + 1
db.put("alice", user)
if user["age"] > 30:
    print("senior")

# everybase
tree = Seq(
    User.age.set(User.age + 1),
    If(User.age > 30, Print("senior")),
)
await tree.execute(ctx)
```

Why trees? Because trees are **data**. You can inspect them, transform them, optimize them, add logging, wrap them in transactions — all before execution.

---

## The Three Primitives

Everything in everybase is built from three orthogonal primitives:

| Primitive | Question it answers | What it does |
|-----------|-------------------|-------------|
| **Term**  | *What* happens?   | Computes values |
| **Flow**  | *When* does it run? | Controls ordering |
| **Span**  | *Which* resources? | Scopes context |

They compose freely:

- Flows contain Terms (ordering computation)
- Spans wrap Flows or Terms (scoping resources)
- Terms never contain Flows (computation doesn't impose order)

Let's learn each one.

---

## Part 1: Terms — Computation

A **Term** is a node that produces a value when executed. Terms compose lazily — building a term tree does nothing until you call `.execute(ctx)`.

### Values: the simplest Terms

A Value wraps a Python literal or a computation:

```python
from everybase.abc import IntValue, FloatValue, StrValue, BoolValue

# Literal values
price = FloatValue(99.95)
name = StrValue("Alice")
count = IntValue(3)
```

Values are Terms, so they support `.execute()`:

```python
from everybase import Context

ctx = Context()
result = await price.execute(ctx)  # 99.95
```

### Expressions: composing Terms

Terms support Python operators. Each operator builds a **new tree node** — nothing executes yet:

```python
price = FloatValue(99.95)
quantity = IntValue(3)
tax_rate = FloatValue(0.08)

subtotal = price * quantity        # FloatValue(MulOp(price, quantity))
tax = subtotal * tax_rate          # FloatValue(MulOp(subtotal, tax_rate))
total = subtotal + tax             # FloatValue(AddOp(subtotal, tax))
is_expensive = total > 250         # BoolValue(GtOp(total, 250))
```

The entire expression is a tree. Execute it to get the result:

```python
print(await total.execute(ctx))         # 323.838
print(await is_expensive.execute(ctx))  # True
```

### What operations are available?

Values inherit operations from their **type base**. For example, `IntValue` inherits from `IntType` which provides:

- **Arithmetic**: `+`, `-`, `*`, `/`, `//`, `%`, `**`, `-x`, `abs()`
- **Comparison**: `==`, `!=`, `<`, `>`, `<=`, `>=`
- **Logical**: `.and_()`, `.or_()`, `.not_()`
- **Conversion**: `.to_str()`, `.to_float()`, `.to_bool()`

String values get `.upper()`, `.lower()`, `.split()`, `.startswith()`, `.endswith()`, `.replace()`, etc.

Lists get `.len()`, `.first()`, `.last()`, `.map()`, `.filter()`, `.sorted()`, etc.

All of these return new Terms — they never execute eagerly.

---

## Part 2: Flows — Ordering

A **Flow** controls *when* its children run. Flows don't produce values — they're transparent wrappers around other executables.

### Sequential execution

```python
from everybase.abc import Seq, Print

greeting = Seq(
    Print("hello"),
    Print("world"),
)
await greeting.execute(ctx)
# [Print:hello]
# [Print:world]
```

### Conditionals

```python
from everybase.abc import If

score = IntValue(85)

result = Seq(
    If(
        score > 90,
        Print("excellent"),
        Print("good"),
    ),
)
await result.execute(ctx)
# [Print:good]
```

### Loops

```python
from everybase.abc import ForRange, While

# Counted loop
ticks = ForRange(0, 5, Print("tick!"))
await ticks.execute(ctx)

# While loop (needs a mutable condition — see Refs below)
```

### Error handling

```python
from everybase.abc import TryCatch, Retry

# Try/catch — catch handler receives ctx with "error" tag
safe = TryCatch(
    risky_operation,
    catch=Print("caught error"),
)

# Retry with exponential backoff
resilient = Retry(
    flaky_operation,
    max_attempts=5,
    delay=1.0,
    backoff=2.0,
)
```

### Parallel execution

```python
from everybase.abc import Parallel, Race

# Run all concurrently
both = Parallel(task_a, task_b)

# First to finish wins (cancels the rest)
winner = Race(producer, consumer)
```

### Full flow catalog

| Flow | What it does |
|------|-------------|
| `Seq(a, b, c)` | Run in order |
| `If(cond, then, else_)` | Branch |
| `While(cond, body)` | Loop while true |
| `DoWhile(cond, body)` | Loop at least once |
| `Forever(body)` | Infinite loop |
| `Switch(sel, {1: a, 2: b})` | Multi-branch |
| `ForRange(start, stop, body)` | Counted loop |
| `ForEach(items, body)` | Iterate collection |
| `Parallel(a, b)` | Concurrent (all) |
| `Race(a, b)` | Concurrent (first wins) |
| `TryCatch(body, catch=h)` | Exception handling |
| `Retry(body, max_attempts=3)` | Retry with backoff |
| `Delay(seconds)` | Sleep |
| `Timeout(seconds, body)` | Time limit |
| `Print(msg, val)` | Print to stdout |
| `Log(msg, level="info")` | Structured logging |

---

## Part 3: Refs — Storage Locations

So far our Terms only use literals. Real applications read and write **storage**. That's where **Refs** come in.

A Ref is a Term that points to a location. It has two key operations:

- `ref.get()` — read the value (returns a typed Value Term)
- `ref.set(v)` — write a value (returns a Command Term)

Both return Terms — they don't execute immediately.

### Shapes: declaring your data structure

A **Shape** declares the structure of your data using slots:

```python
from everybase.shape import Shape
import eb_dict as d

class User(Shape):
    name = d.StrRef.slot()
    age = d.IntRef.slot()
    score = d.FloatRef.slot()
```

Each slot creates a Ref. Access it on the class:

```python
User.name   # → StrRef pointing to "name" in User's storage
User.age    # → IntRef pointing to "age" in User's storage
```

### Reading and writing

```python
# Build a tree that writes, then reads
tree = Seq(
    User.name.set("Alice"),
    User.age.set(30),
    Print("name", User.name),       # User.name used as a Term = implicit .get()
    Print("age", User.age),
)
```

### Expressions with Refs

Because `.get()` returns a typed Value, you get the full type algebra:

```python
# All of these build expression trees — nothing executes yet
next_age = User.age + 1
is_adult = User.age >= 18
greeting = StrValue("Hello, ") + User.name
upper_name = User.name.upper()
```

Use them in Flows:

```python
tree = Seq(
    User.name.set("Alice"),
    User.age.set(30),
    User.age.set(User.age + 1),          # increment
    If(User.age > 30, Print("senior")),
    Print("greeting", StrValue("Hi ") + User.name),
)
```

### Nested Shapes

Shapes can nest:

```python
import eb_dict as d
from everybase.shape import Shape

class Address(Shape):
    city = d.StrRef.slot()
    zip_code = d.StrRef.slot()

class User(Shape):
    name = d.StrRef.slot()
    home = d.ShapeRef.slot(Address)

# Navigate into nested shape
tree = Seq(
    User.home.city.set("Portland"),
    Print("city", User.home.city),
)
```

### Collections

```python
class Team(Shape):
    members = d.ShapesListRef.slot(User)
    roles = d.ShapesDictRef.slot(User)

# List access by index
Team.members[0].name

# Dict access by key
Team.roles["admin"].name
```

---

## Part 4: Context — Runtime Environment

A Term tree is just data. To execute it, you need a **Context** — the runtime environment that provides storage handles.

Context is an **immutable, tag-keyed store**. You bind values to tag sets, then look them up:

```python
from everybase import Context

ctx = Context()
ctx = ctx.bind(my_database, StorageProtocol)       # 1 tag
ctx = ctx.bind(order_db, StorageProtocol, Order)    # 2 tags (scoped)
```

Lookup uses subscript syntax:

```python
ctx[StorageProtocol]              # → my_database
ctx[StorageProtocol, Order]       # → order_db
```

### Setting up Context for the dict substrate

The dict substrate stores data in plain Python dicts:

```python
import eb_dict as d
from everybase import Context
from everybase.shape import Shape

class User(Shape):
    name = d.StrRef.slot()
    age = d.IntRef.slot()

# Create the data bag and bind it to context
data = {}
ctx = Context().bind(data, dict, User)

# Now execute
tree = Seq(
    User.name.set("Alice"),
    User.age.set(30),
    Print("name", User.name),
)
await tree.execute(ctx)

# The dict was mutated
print(data)  # {'name': 'Alice', 'age': 30}
```

### Multi-store Context

Different Shapes can use different storage:

```python
users_data = {}
orders_data = {}

ctx = (Context()
    .bind(users_data, dict, User)
    .bind(orders_data, dict, Order)
)
```

Each Ref knows its Shape and looks up the right store automatically.

### Lazy factories

For expensive resources, bind a factory that's called only on first access:

```python
ctx = ctx.lazy(lambda: open_database_connection(), DatabaseType)
# Connection not opened yet

db = ctx[DatabaseType]   # Now the factory runs
db2 = ctx[DatabaseType]  # Cached — same connection
```

---

## Part 5: Spans — Resource Scoping

A **Span** is an invisible bracket that scopes context for its children. Think of it like a `with` block:

```python
# Python
with db.transaction() as txn:
    txn.set("name", "Alice")
    txn.set("age", 30)
    txn.commit()

# everybase
Atomic(
    Seq(
        User.name.set("Alice"),
        User.age.set(30),
    ),
    scope=User,
)
```

### Atomic: the PV transaction Span

When using the PV substrate (persistent key-value storage), `Atomic` handles transactions:

```python
import eb_virtuals as ebv
from everybase.shape import Shape

class AppState(Shape):
    name = ebv.StrRef.slot()
    counter = ebv.IntRef.slot()

tree = ebv.Atomic(
    Seq(
        AppState.name.set("Alice"),
        AppState.counter.set(0),
    ),
    scope=AppState,
)
```

On enter: opens a transaction lazily
On success: commits
On failure: aborts

Smart behavior:

- If all children are read-only, opens a snapshot instead (cheaper)
- If no child accesses storage, nothing is opened at all

### auto_atomic: automatic transaction wrapping

Instead of manually wrapping in `Atomic`, use the `auto_atomic` deformation:

```python
# Write your tree without worrying about transactions
tree = Seq(
    AppState.name.set("Alice"),
    AppState.counter.set(AppState.counter + 1),
    Print("name", AppState.name),
)

# auto_atomic wraps storage-accessing subtrees in Atomic spans
safe_tree = ebv.auto_atomic(tree)
await safe_tree.execute(ctx)
```

### Span transparency

Spans are **transparent** — removing them doesn't change what's computed, only what's shared. This is a design invariant: Spans scope resources, they don't change semantics.

---

## Part 6: Sentinels — Absence and Failure

everybase uses **sentinels** instead of exceptions for data-level issues:

| Sentinel | Meaning | When returned |
|----------|---------|--------------|
| `EMPTY` | Value doesn't exist | Reading a missing key |
| `INVALID` | Operation not applicable | Adding a string to a number |

Sentinels propagate automatically. If any operand of an operation is a sentinel, the result is `INVALID` without calling the operation:

```python
from everybase import EMPTY, is_empty, is_sentinel

# If User.age doesn't exist in storage:
result = await (User.age + 1).execute(ctx)
# result is INVALID (not an exception)

is_sentinel(result)  # True
is_empty(result)     # False (it's INVALID, not EMPTY)
```

This lets you handle missing data without try/except everywhere.

---

## Part 7: Morphisms — Under the Hood

When you write `User.age + 1`, everybase builds a tree node called a **Morphism**. Understanding morphisms helps when writing custom operations.

A Morphism transforms inputs to outputs:

```python
# This expression:
User.age + 1

# Builds this tree:
IntValue(AddOp(User.age.get(), IntValue(1)))
```

### Purity

Every morphism is either:

- **Operation** — pure, no side effects (reads, arithmetic, comparisons)
- **Command** — impure, mutates state (writes, deletes)

everybase uses purity to optimize: pure subtrees can use read-only snapshots.

### Arity

| Base class | Operands | Example |
|-----------|----------|---------|
| `UnaryOperation` | 1 | `NegOp(x)` → `-x` |
| `BinaryOperation` | 2 | `AddOp(x, y)` → `x + y` |
| `TernaryOperation` | 3 | rare |

### Writing a custom morphism

```python
from everybase import BinaryOperation

class DistanceOp(BinaryOperation[float]):
    """Euclidean distance between two points."""

    def apply(self, a: tuple, b: tuple) -> float:
        return ((a[0]-b[0])**2 + (a[1]-b[1])**2) ** 0.5
```

Rules:

1. Pass data operands to `super().__init__()` — they become children
2. Store configuration as attributes (not children)
3. `apply()` receives resolved Python values, not Terms

---

## Part 8: Primitive Refs — Injecting Runtime Values

Sometimes you need to pass runtime values (not from storage) into a term tree. **Primitive Refs** solve this — they resolve by name from Context.

```python
from everybase.abc.refs import StrRef, IntRef

error = StrRef("error")
attempt = IntRef("attempt")

# Bind values into context by name
ctx = Context().bind("connection refused", "error").bind(3, "attempt")

# Refs read from context
msg = await error.get().execute(ctx)       # "connection refused"
num = await attempt.get().execute(ctx)     # 3
```

This is how Retry hooks work — the hooks receive a context extended with `"error"` and `"attempt"` tags:

```python
from everybase.abc import Retry, Print
from everybase.abc.refs import StrRef, IntRef

error = StrRef("error")
attempt = IntRef("attempt")

resilient = Retry(
    flaky_operation,
    max_attempts=5,
    delay=1.0,
    on_attempt_fail=Print("retry", error.get(), attempt.get()),
    on_success=Print("ok after", attempt.get()),
    on_fail=Print("gave up after", attempt.get()),
)
```

---

## Part 9: Tree Transforms — Rewriting Before Execution

Because term trees are data, you can transform them before execution. everybase provides tools for this:

```python
from everybase import map_nodes, find, preorder, format_tree
```

### Inspecting trees

```python
tree = Seq(
    User.name.set("Alice"),
    If(User.age > 18, Print("adult")),
)

# Pretty-print
print(format_tree(tree))

# Find all nodes matching a predicate
refs = find(tree, lambda n: isinstance(n, Ref))

# Walk in order
for node in preorder(tree):
    print(type(node).__name__)
```

### Transforming trees

```python
from everybase import map_nodes

# Add logging to every Print node
def add_prefix(node):
    if isinstance(node, Print):
        return Log(f"[APP] {node}", level="info")
    return node

logged_tree = map_nodes(tree, add_prefix)
```

### annotate_retries: a built-in transform

`annotate_retries` auto-adds logging hooks to bare `Retry` nodes:

```python
from everybase import annotate_retries

bare = Retry(flaky_op, max_attempts=3)
print(bare.has_hooks)  # False

annotated = annotate_retries(bare)
print(annotated.has_hooks)  # True
# Now logs WARNING on each failed attempt, ERROR on final failure
```

---

## Part 10: Substrates — Where Data Lives

A **substrate** is a storage backend. everybase ships two:

### eb-dict — In-memory dicts

Simplest substrate. Data lives in plain Python dicts. No persistence, no transactions.

```python
import eb_dict as d
from everybase.shape import Shape

class Counter(Shape):
    value = d.IntRef.slot()
    label = d.StrRef.slot()

data = {}
ctx = Context().bind(data, dict, Counter)

await Seq(
    Counter.value.set(0),
    Counter.label.set("clicks"),
    Counter.value.set(Counter.value + 1),
    Print("count", Counter.value),
).execute(ctx)
```

Great for: prototyping, testing, in-memory state.

### eb-virtuals — Persistent key-value

Full substrate with persistence (RocksDB), transactions, snapshots, and reactivity.

```python
import eb_virtuals as ebv
from everybase.shape import Shape

class AppState(Shape):
    name = ebv.StrRef.slot()
    counter = ebv.IntRef.slot()

# Setup storage
from virtuals.tkv.tkv.storage import StorageProtocol
from eb_virtuals.presets import text_storage

with text_storage(".db") as storage:
    ctx = Context().bind(storage, StorageProtocol)

    tree = ebv.auto_atomic(Seq(
        AppState.name.set("Alice"),
        AppState.counter.set(0),
        AppState.counter.set(AppState.counter + 1),
        Print("name", AppState.name),
        Print("counter", AppState.counter),
    ))
    await tree.execute(ctx)
```

Features:

- **Transactions** via `Atomic` span (auto-commit/abort)
- **Snapshots** for read-only access (auto-detected for pure subtrees)
- **Reactivity** via `.on_change()` (see reactive section below)
- **auto_atomic** transform to auto-wrap in transactions

### Mixing substrates

Different Shapes can use different substrates in the same tree:

```python
import eb_dict as d
import eb_virtuals as ebv

class Config(Shape):         # in-memory
    debug = d.BoolRef.slot()

class UserDB(Shape):         # persistent
    name = ebv.StrRef.slot()

config_data = {}
ctx = (Context()
    .bind(config_data, dict, Config)
    .bind(storage, StorageProtocol)
)
```

---

## Part 11: Reactive — Responding to Changes

The PV substrate supports **observability** — you can react to value changes:

```python
import eb_virtuals as ebv
from everybase.shape import Shape
from everybase.shape.flows import ReactWhile

class Sensor(Shape):
    temperature = ebv.FloatRef.slot()

# Producer writes sensor data in a loop
producer = Seq(
    Sensor.temperature.set(18.0),
    ForRange(0, 20, Seq(
        Sensor.temperature.set(Sensor.temperature + 1.5),
        Delay(0.01),
    )),
)

# Consumer reacts to every change
consumer = ReactWhile(
    Sensor.temperature.on_change(),       # trigger
    Sensor.temperature < 40.0,            # keep going while
    If(
        Sensor.temperature > 30.0,
        Print("WARNING: high temp!", Sensor.temperature),
    ),
)

# Race: producer and consumer run concurrently
# When producer finishes, consumer is cancelled
tree = Race(producer, consumer)
tree = ebv.auto_atomic(tree)
await tree.execute(ctx)
```

---

## Putting It All Together

Here's a complete, runnable example using the dict substrate (no external dependencies):

```python
import asyncio
import eb_dict as d
from everybase import Context
from everybase.abc import ForRange, If, Print, Retry, Seq

from everybase.shape import Shape


class GameState(Shape):
    player = d.StrRef.slot()
    score = d.IntRef.slot()
    level = d.IntRef.slot()


async def main():
    data = {}
    ctx = Context().bind(data, dict, GameState)

    game = Seq(
        # Initialize
        GameState.player.set("Alice"),
        GameState.score.set(0),
        GameState.level.set(1),

        # Play 5 rounds
        ForRange(0, 5, Seq(
            GameState.score.set(GameState.score + 10),
            GameState.level.set(GameState.level + 1),
        )),

        # Check result
        If(
            GameState.score >= 40,
            Print("Winner!", GameState.player, GameState.score),
            Print("Try again", GameState.player),
        ),

        # Final state
        Print("player", GameState.player),
        Print("score", GameState.score),
        Print("level", GameState.level),
    )

    await game.execute(ctx)


asyncio.run(main())
```

---

## Quick Reference

### Imports

```python
# Core
from everybase import Context

# Values
from everybase.abc import IntValue, FloatValue, StrValue, BoolValue

# Flows
from everybase.abc import Seq, If, While, ForRange, ForEach
from everybase.abc import Parallel, Race, TryCatch, Retry
from everybase.abc import Print, Log, Delay, Timeout

# Dict substrate
import eb_dict as d

# PV substrate
import eb_virtuals as ebv

# Shapes
from everybase.shape import Shape

# Tree tools
from everybase import find, map_nodes, format_tree, preorder

# Primitive refs
from everybase.abc.refs import IntRef, StrRef, FloatRef, BoolRef

# Transforms
from everybase import annotate_retries
```

### Context API

```python
ctx = Context()
ctx = ctx.bind(value, Tag)              # eager binding
ctx = ctx.bind(value, Tag1, Tag2)       # multi-tag (scoped)
ctx = ctx.lazy(factory, Tag)            # lazy (called on first access)
val = ctx[Tag]                          # lookup
val = ctx[Tag1, Tag2]                   # scoped lookup
Tag in ctx                              # check existence
ctx.was_opened(Tag)                     # check if lazy was materialized
```

### Shape + Ref patterns

```python
class MyShape(Shape):
    # Scalars
    name = d.StrRef.slot()
    count = d.IntRef.slot()

    # Nested shape
    address = d.ShapeRef.slot(Address)

    # Collections
    items = d.ShapesListRef.slot(Item)
    lookup = d.ShapesDictRef.slot(Entry)

# Read/write
MyShape.name.set("value")       # write (returns Term)
MyShape.name.get()              # read (returns typed Value Term)
MyShape.name                    # shorthand for .get() in most contexts

# Navigate
MyShape.address.city            # nested field
MyShape.items[0].name           # list index
MyShape.lookup["key"].value     # dict key
```

### Execution

```python
# Everything is async
result = await term.execute(ctx)
await flow.execute(ctx)
```
