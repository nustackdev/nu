# Span

A Span scopes its children. It answers: **which** steps are grouped together.

## Core Idea

Spans are transparent brackets. They don't compute anything — removing all Spans from a tree doesn't change what is computed, only what is shared during computation.

```python
from every_pv import Atomic
from every_flow import Seq

# Without Span: two independent writes
Seq(
    User.name.set("Alice"),
    User.age.set(30),
)

# With Span: two writes in one transaction
Atomic(User, DictView,
    Seq(
        User.name.set("Alice"),
        User.age.set(30),
    ),
)
```

## Lifecycle

```
Span.enter(ctx)           -> child_ctx     # create scoped context
  children.execute(child_ctx)              # run children with scoped context
Span.exit_success(ctx)    -> cleanup       # on success
Span.exit_failure(ctx, e) -> cleanup       # on error
```

A Span's `execute` method:

1. Calls `enter(ctx)` to get a child context
2. Runs all children with the child context
3. Calls `exit_success` or `exit_failure` depending on outcome
4. Returns the last child's result (transparency)

## Design Rules

**S1. Span transparency.** Removing Spans doesn't change computation, only sharing.

**B2. Nearest enclosing Span wins.** When a Term needs context, the executor walks up to the first Span that provides it.

**B4. Innermost wins.** Nested Spans override — inner context shadows outer (like lexical scoping).

**C1. Lazy open.** Context is created when the first child that needs it executes, not at Span entry.

**C2. Eager close.** Context is released when the last child that needed it completes, not at Span exit.

## Writing Custom Spans

```python
from everybase import Span, Context

class TimingSpan(Span):
    """Measure execution time of children."""

    def __init__(self, label, *children):
        super().__init__(*children)
        self._label = label
        self._start = None

    def enter(self, ctx: Context) -> Context:
        import time
        self._start = time.monotonic()
        return ctx  # passthrough context

    def exit_success(self, ctx: Context) -> None:
        import time
        elapsed = time.monotonic() - self._start
        print(f"[{self._label}] {elapsed:.3f}s")

    def exit_failure(self, ctx: Context, error: Exception) -> None:
        import time
        elapsed = time.monotonic() - self._start
        print(f"[{self._label}] FAILED after {elapsed:.3f}s: {error}")
```
