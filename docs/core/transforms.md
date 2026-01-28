# Tree Transforms

The tree is data. Groups don't change computation (rule S2).
Therefore: **functions over trees are the extension mechanism.**

Cross-cutting concerns are not built into the core.
They are tree → tree functions applied before execution.

---

## What a transform is

A function that takes a valid tree and returns a valid tree.
It can inspect, wrap, rewrite, or insert nodes.

```python
type Transform = Callable[[Unit], Unit]
```

Transforms compose by function composition:

```python
app = Seq(read(a), write(b), notify())

app = add_cancellation(app)
app = add_logging(app)
app = add_retry(app, max=3)
```

Or composed as a pipeline:

```python
pipeline = compose(add_cancellation, add_logging, add_retry)
app = pipeline(app)
```

---

## Examples

### Cancellation

Inserts cancellation checks at Flow→Unit boundaries:

```python
# Before:
Seq(step_a, step_b, step_c)

# After add_cancellation:
Seq(
    Cond(cancelled(), raise_cancel(), step_a),
    Cond(cancelled(), raise_cancel(), step_b),
    Cond(cancelled(), raise_cancel(), step_c),
)
```

### Logging

Inserts log Terms around Flow children:

```python
# Before:
Seq(step_a, step_b)

# After add_logging:
Seq(
    log("enter step_a"), step_a, log("exit step_a"),
    log("enter step_b"), step_b, log("exit step_b"),
)
```

### Retry

Wraps fallible units in retry logic:

```python
# Before:
Seq(fetch_data(), process())

# After add_retry:
Seq(
    Loop(retry_pred(max=3), fetch_data()),
    process(),
)
```

### Others

Same pattern applies to timeout, tracing, circuit breaking,
rate limiting, auth injection, metrics — any cross-cutting concern.

---

## Why this works

The tree being pure data makes transforms natural:

- **Grammar-preserving.** Output must be a valid tree.
  Composition rules (R1-R3) still hold.

- **Composable.** Transforms are functions. They compose.
  Order may matter (logging before retry ≠ retry before logging).

- **Safe when adding only Groups.** Since Groups don't change computation
  (rule S2), transforms that only insert Groups preserve semantics.

- **Inspectable.** The tree after transforms is still data.
  It can be printed, analyzed, diffed, tested — before execution.

---

## Core vs. transforms

The core defines the language: Term, Flow, Group, resolution, execution.
Transforms define the ecosystem: everything else.

```
Core (minimal, stable):
  Primitives: Term, Flow, Group
  Resolution and lifetime
  Executor (tree walk)

Transforms (open, composable):
  Cancellation, logging, retry, timeout,
  tracing, circuit breaking, rate limiting, ...
```

If it can be expressed as tree → tree, it belongs in transforms, not core.
