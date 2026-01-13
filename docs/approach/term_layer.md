# Term Layer — Philosophy

The term layer is a **protocol layer**. It defines contracts for computation over data.

Minimal implementation. Maximum extensibility.

## Core Split

Two kinds of terms:

| Term | What It Is | Example |
|------|------------|---------|
| **LValue** | Location (where data lives) | `Market.price` |
| **RValue** | Expression (what computes) | `Market.price.get() + 100` |

LValues resolve to paths. RValues execute to produce results.

## The Protocols

```text
Term                        - executable node
├── LValue                  - addressable location
│   └── Ref                 - typed reference
│       ├── ViewRef         - points to container
│       └── PrimitiveRef    - points to leaf value
└── RValue                  - evaluable expression
    ├── TypedValue          - typed wrapper (IntValue, DatetimeValue, etc.)
    └── Computation         - logic
        ├── Operation       - pure (no side effects)
        └── Command         - impure (mutations)
```

Everything has `execute(ctx)` and `is_pure`.

## Pure vs Impure

```python
# Pure - deterministic, cacheable, reorderable
price = Market.price.get()           # Operation
total = price + tax                   # Operation
expensive = price > 1000              # Operation

# Impure - side effects, order matters, transactional
Market.price.set(150.0)              # Command
Market.orders.clear()                 # Command
```

Purity is declared, not inferred.

## Lazy Evaluation

Terms build trees. Execution is explicit.

```python
# Build expression (nothing runs yet)
expr = price.get() * quantity.get() + tax.get()

# Execute when ready
result = expr.execute(ctx)
```

## Extension Points

Layer 4 defines protocols. You implement them.

| You Create | By Extending |
|------------|--------------|
| Domain types | `TypedValue` + capability bases |
| Storage refs | `PrimitiveRef` or `ViewRef` |
| Pure logic | `Operation` |
| Mutations | `Command` |

```python
# Custom type
class MoneyValue(NumericBase, CoreBase, TypedValue[Money]):
    def to_cents(self) -> IntValue:
        return IntValue(MethodCallOp(self, "to_cents"))

# Custom ref
class MoneyRef(CollectionItemRefBase[Money, MoneyValue], PrimitiveRef):
    def get(self) -> MoneyValue:
        return MoneyValue(GetOp(self))
```

## Capability Composition

Types gain behavior through bases:

| Base | Provides |
|------|----------|
| `CoreBase` | `ifelse()`, `is_empty()`, `or_default()` |
| `NumericBase` | `+`, `-`, `*`, `/`, `**`, `%` |
| `ComparisonBase` | `>`, `<`, `>=`, `<=` |
| `LogicalBase` | `and_()`, `or_()`, `not_()` |
| `EqualableBase` | `eq()`, `ne()` |

No inheritance hierarchies. Just composition.

## Naming

| Term | Meaning |
|------|---------|
| `ref` | Location in data tree |
| `value` | Typed expression result |
| `operation` | Pure computation |
| `command` | Impure mutation |

Suffixes: `*Op` (operation), `*Cmd` (command), `*Value` (typed wrapper), `*Ref` (reference).

## What Layer 4 Does NOT Do

- **No view logic** — Layer 3 (dict/list/set semantics)
- **No hierarchy** — Layer 2 (container rules)
- **No storage** — Layer 1 (KV access)
- **No shapes** — Layer 5 (slots, models)

Layer 4 knows expressions. Not structure. Not storage. Not schemas.

---

Protocols over implementations. Composition over inheritance. Build anything.
