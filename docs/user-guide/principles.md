# Principles

Core design principles for building everybase apps. These are non-negotiable.

## Terms over injection

Express logic as term trees, not injected Python functions.

```python
# Wrong: inject a function to do the work
result = FuncCallOp(extract_mint, tx)

# Right: compose terms that do the work
mint = ListValue(tx.token_balances.get()).pluck_("mint").filter_(bool).first()
```

`FuncCallOp` is an escape hatch, not a building block. Every time you reach for it, ask: can this be a term? If the answer is "not yet", consider adding the missing primitive.

## Primitives over helpers

When term algebra can't express something, add a primitive — don't normalize injection.

A 5-line helper behind `FuncCallOp` is acceptable as a temporary bridge. A pattern of helpers is a signal that primitives are missing. Fill the gap in the type system, then delete the helper.

```python
# Temporary: helper for cross-dict delta (no dict-join primitive yet)
token_delta = IntValue(FuncCallOp(_max_token_delta, pre_dict, post_dict))

# Future: once a primitive exists, replace
token_delta = pre_dict.delta_by_(post_dict).max_(key=lambda d: abs(d))
```
