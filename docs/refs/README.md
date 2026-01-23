# Ref System

The Ref system provides typed references to locations where values live. It is the LValue branch of the Term hierarchy.

## Core Vocabulary

| Verb | Purpose | Layer |
|------|---------|-------|
| `resolve(ctx)` | Build identity/location (WHERE) | Ref protocol |
| `fetch(ctx)` | Extract value from location (WHAT) | Ref protocol |
| `execute(ctx)` | Polymorphic Term entry point | Term interface |
| `get(ctx)` | User-friendly value access | Shapes, Views (user-facing) |

Three internal verbs, one user-facing verb. Less but better.

## Design Principles

1. **Hierarchy and structure** - Clear layers, each adds ONE concept
2. **Clean scope of capabilities** - Traits are separate, composed explicitly
3. **Coherence** - One pattern everywhere: `Substrate + TypeBase = ConcreteRef`
4. **Minimal protocol** - `every.Ref` has no substrate assumptions

## Architecture

```
every.Ref[T]  (pure protocol)
├── resolve(ctx) → Location     # abstract - WHERE
├── fetch(ctx) → T | Sentinel   # abstract - WHAT
└── execute(ctx) → fetch(ctx)   # concrete - Term compatibility
```

See [architecture.md](./architecture.md) for the full hierarchy.

## Layers

| Layer | Location | Purpose |
|-------|----------|---------|
| 0 | `every/term/ref.py` | Pure protocol |
| 1 | `everybase/traits/` | Operator mixins (Numeric, Comparable, etc.) |
| 2 | `everybase/refs/` | Type bases (IntRefBase, StrRefBase, etc.) |
| 3 | Substrate packages | Storage implementation (PyRef, PVRefBase, etc.) |
| 4 | Concrete refs | Substrate + TypeBase combined |

See [layers.md](./layers.md) for detailed layer documentation.

## Substrates

A substrate defines WHERE values live and HOW to access them:

| Substrate | Package | Context | Description |
|-----------|---------|---------|-------------|
| Python memory | `everybase/py/` | Empty | Values in Python runtime |
| PV storage | `every_pv/` | root_view + transaction | Values in view hierarchy |
| (future) Notion | `every_notion/` | HTTP client | Values in Notion pages |

See [substrates.md](./substrates.md) for substrate implementation guide.

## Quick Reference

```python
# User code - building expressions
x = IntRef(5)
y = IntRef(10)
z = x + y        # → IntRef(AddOp(x, y)) - lazy expression

# Execution - actually compute
value = z.execute(ctx)  # → 15

# Or equivalently for refs
value = z.fetch(ctx)    # → 15
```
