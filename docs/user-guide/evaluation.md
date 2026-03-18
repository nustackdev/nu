# Evaluation

How term trees evaluate inside flows, and how to avoid the main pitfall.

## Core Rule

A term is a computation tree, not a cached result. Every time the flow engine encounters a term, it walks the tree and evaluates from scratch.

```python
# This is NOT "compute once, store in result"
# This is "here's a recipe for computing something"
result = DictValue(FuncCallOp(my_func, some_ref.get()))

# Every use of `result` re-runs my_func with whatever some_ref.get()
# returns AT THAT MOMENT — not when the variable was assigned
```

Python variable names are misleading. `final_price`, `enriched_trades`, `result` — they look like cached values but they're branches of a computation tree. Each `.set(term)` in a Seq triggers a fresh evaluation of the entire term subtree.

## The Re-evaluation Trap

If a term tree reads from a ref and that ref is mutated earlier in the same Seq, subsequent evaluations see the mutated value. The term is re-evaluated, not replayed.

```python
# BUG: result reads token.curve.get() — a mutable ref
result = DictValue(FuncCallOp(apply_trades, token.curve.get().to_dict(), trades))

f.Seq(
    # First evaluation: reads old curve, applies trades, stores new curve
    token.curve.set(LocalCurveValue.from_dict(result["curve"])),

    # Second evaluation: reads NEW curve (just set above!), applies trades AGAIN
    token.price.set(result["trades"].last()["price"]),  # WRONG — double-applied
)
```

This is not "just slow" — it produces **wrong data**. If the term tree contains Commands, they execute multiple times, corrupting state.

## Cache Before Reuse

When a computation is needed in multiple places, store it in a scratch slot first, then read from storage everywhere else.

```python
# RIGHT: compute once → store → read from storage
f.Seq(
    # Single evaluation — FuncCallOp runs once, result stored
    s._scratch.set(FuncCallOp(compute, input_ref.get())),

    # All downstream reads go through storage (not the FuncCallOp tree)
    output_a.set(s._scratch.get()["field_a"]),
    output_b.set(s._scratch.get()["field_b"]),
)
```

`s._scratch.get()` is a storage read — it returns the frozen stored value, not a re-evaluation of the computation. Ordering of subsequent `.set()` calls no longer matters.

**Rule**: any term referenced more than once MUST go through storage first. Not for performance — for correctness.

### Scratch Slots

Use `_` prefixed slots on the Shape for intermediate data that isn't part of the data model:

```python
class MyState(Shape):
    # Data model
    count = pv.IntRef.slot()
    items = pv.ListRef.slot(str)

    # Scratch (internal, not part of data model)
    _loop_idx = pv.IntRef.slot()
    _computation_result = pv.DictRef.slot(str, object)
```

## Ref Reads vs Term Trees

A ref `.get()` reads from storage — deterministic, stable, unaffected by mutations to other refs. A term tree walks back to its leaves and evaluates everything, including any `.get()` calls embedded in it.

```python
# STABLE: reads from storage, always returns what was last .set()
value = s.my_slot.get()

# UNSTABLE: walks entire tree, re-evaluates all embedded .get() calls
value = DictValue(FuncCallOp(func, s.other_slot.get()))
```

Design flows so that the "compute" step and the "read" step are separated by storage:

```
compute (FuncCallOp) → .set() into scratch → .get() from scratch → use
```

## Python Variables for Composition

Using Python variables for tree fragments is fine — they're just shorthand for tree paths:

```python
token = s.tokens[q.current_mint]  # navigation shorthand
snap = token.snapshots[-1]        # same
```

But don't confuse these with "having a value." They're ref paths, not data. The key distinction:
- **Ref paths** (`token.price_lamports`) — navigation, always safe to reuse
- **Computation terms** (`FuncCallOp(...)`, `ref.get().method()`) — trees, dangerous to reuse without caching

## FuncCallOp Safety

`FuncCallOp` is an escape hatch (see [principles](principles.md)). When you do need it:

1. Keep it pure (no side effects)
2. Store the result immediately in a scratch slot
3. Never reference the FuncCallOp term from multiple places in a Seq

## Flow Structure Pattern

For processors that compute, update, and snapshot:

```python
f.Seq(
    # 1. Compute and cache (single FuncCallOp evaluation)
    s._result.set(FuncCallOp(compute, current_state.get(), inputs)),

    # 2. Update state from cached result (order doesn't matter now)
    state.set(s._result.get()["new_state"]),
    metric_a.set(s._result.get()["metric_a"]),
    metric_b.set(s._result.get()["metric_b"]),

    # 3. Build snapshot from updated state refs
    snapshots.append({}),
    snapshots[-1].field.set(state.metric),
)
```

The key insight: step 2 can set `state` at any position because `s._result.get()` reads from storage, not from `state.get()`. The mutation of `state` doesn't affect the cached result.
