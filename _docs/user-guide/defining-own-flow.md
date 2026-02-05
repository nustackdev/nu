# Defining Your Own Flow

How to create custom Flow nodes that compose with the rest of the system.

## Pattern

A custom Flow inherits from `Flow` and implements `execute(ctx)`:

```python
from everybase import Flow, Context

class MyFlow(Flow):
    def __init__(self, *children):
        super().__init__(*children)  # MUST register children

    async def execute(self, ctx: Context) -> None:
        # orchestrate children
        for child in self.children:
            await child.execute(ctx)
```

The key rules:

1. **Always call `super().__init__()` with children** — this registers them in the tree
2. **Parameters that influence control flow become children** — visible to tree transforms
3. **Use `ensure_term()` to wrap literals** — so Python values become tree nodes
4. **Return `None`** — Flows order execution, they don't produce values

## Example: Rate-Limited Sequential Execution

```python
from everybase import Flow, Context
from everybase.abc import ensure_term
import asyncio


class RateLimitedSeq(Flow):
    """Execute children sequentially with a delay between each."""

    def __init__(self, delay, *children):
        # delay becomes a child node (visible to tree transforms)
        super().__init__(ensure_term(delay), *children)

    async def execute(self, ctx: Context) -> None:
        delay = await self.children[0].execute(ctx)
        for child in self.children[1:]:
            await child.execute(ctx)
            await asyncio.sleep(delay)
```

Usage:

```python
tree = RateLimitedSeq(
    0.5,  # 500ms between each
    fetch_page_1,
    fetch_page_2,
    fetch_page_3,
)
await tree.execute(ctx)
```

## Example: Poll Until Condition

```python
import asyncio
from everybase import Flow, Context
from everybase.abc import ensure_term


class PollUntil(Flow):
    """Poll body until condition is true, with configurable interval."""

    def __init__(self, condition, body, *, interval=1.0, max_attempts=30):
        super().__init__(
            ensure_term(condition),
            body,
            ensure_term(interval),
            ensure_term(max_attempts),
        )

    async def execute(self, ctx: Context) -> None:
        condition = self.children[0]
        body = self.children[1]
        interval = await self.children[2].execute(ctx)
        max_attempts = await self.children[3].execute(ctx)

        for _ in range(max_attempts):
            await body.execute(ctx)
            if await condition.execute(ctx):
                return
            await asyncio.sleep(interval)

        raise TimeoutError(f"Condition not met after {max_attempts} attempts")
```

Usage:

```python
tree = PollUntil(
    Account.status.get() == "confirmed",
    check_transaction_status,
    interval=2.0,
    max_attempts=15,
)
```

## Example: With Side-Effect Hooks

```python
from everybase import Flow, Context, Executable


class WithCallback(Flow):
    """Run a tree, then call a Python callback with the result."""

    def __init__(self, body: Executable, *, on_complete=None, on_error=None):
        super().__init__(body)
        self._on_complete = on_complete
        self._on_error = on_error

    async def execute(self, ctx: Context) -> None:
        try:
            await self.children[0].execute(ctx)
            if self._on_complete:
                self._on_complete()
        except Exception as e:
            if self._on_error:
                self._on_error(e)
            raise
```

Note: `on_complete` and `on_error` are Python callables, not tree nodes — they don't become children because they're not part of the expression tree. Only values that participate in the tree algebra should be children.

## Design Guidelines

### Children vs Attributes

**Make it a child** if it:

- Is a Term/Flow/Span that should be visible to tree transforms
- Could be a literal OR a computed value (wrap with `ensure_term()`)
- Affects control flow

**Make it an attribute** if it:

- Is configuration that never changes (like a string label)
- Is a Python callable (callback, factory)
- Should not be walked by tree utilities

### Optional Children

Track which optional children exist with flags:

```python
class MyFlow(Flow):
    def __init__(self, body, on_error=None):
        self._has_error_handler = on_error is not None
        children = [body]
        if on_error is not None:
            children.append(on_error)
        super().__init__(*children)

    async def execute(self, ctx: Context) -> None:
        try:
            await self.children[0].execute(ctx)
        except Exception:
            if self._has_error_handler:
                await self.children[1].execute(ctx)
            else:
                raise
```

### State Binding with Refs

Let callers bind intermediate results to Refs:

```python
class MyFlow(Flow):
    def __init__(self, body, *, result_ref=None):
        super().__init__(body)
        self._result_ref = result_ref

    async def execute(self, ctx: Context) -> None:
        await self.children[0].execute(ctx)
        if self._result_ref is not None:
            await self._result_ref.set("done").execute(ctx)
```

### Bridging Callbacks to Async

For integrating with callback-based systems (like reactive subscriptions):

```python
import asyncio
from everybase import Flow, Context


class WaitForEvent(Flow):
    """Wait for an external event, then run body."""

    def __init__(self, subscribe_fn, body):
        super().__init__(body)
        self._subscribe_fn = subscribe_fn

    async def execute(self, ctx: Context) -> None:
        loop = asyncio.get_running_loop()
        event = asyncio.Event()

        def on_event():
            loop.call_soon_threadsafe(event.set)

        unsub = self._subscribe_fn(on_event)
        try:
            await event.wait()
            await self.children[0].execute(ctx)
        finally:
            unsub()
```
