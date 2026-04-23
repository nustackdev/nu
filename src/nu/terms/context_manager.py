"""ContextManager - bracket around a body.

One of the four direct Nu kinds:

    Nu
    ├── Ref
    ├── Interaction
    ├── Form
    └── ContextManager    (this module)

Pure structural. No fabric interaction, no computation of its own. Brackets
child evaluation with `before` / `after` / `after_failure` hooks. Role comes
from what the hooks do (commit a transaction -> Command; release a snapshot
-> Query) and from mixing with Command / Query bases.

Typical composition:
    class Transaction(ContextManager, Command): ...
    class Snapshot(ContextManager, Query[T]): ...
"""

from __future__ import annotations

from abc import ABC
from contextlib import closing
from typing import TYPE_CHECKING, Any

from .nu import Nu
from .types import Mode


if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Generator

    from ..context import Context


__all__ = [
    "ContextManager",
]


class ContextManager(Nu, ABC):
    """Brackets children with before/after hooks.

    Hooks:
        before(ctx) -> ctx        enter. return scoped ctx for the body.
        after(ctx)                exit, clean path.
        after_failure(ctx, exc)   exit, exception path.

    `aopen` runs children under the bracket. `GeneratorExit` (raised when a
    consumer closes the generator early, e.g. NAryScalar taking a single yield
    from a scope-producing child) counts as clean and routes to `after`.
    Real exceptions route to `after_failure`.
    """

    async def aopen(self, ctx: Context) -> AsyncGenerator[Any, None]:
        scoped_ctx = self.before(ctx)
        try:
            for child in self._children:
                async for v in self._adispatch_child(child, scoped_ctx):
                    yield v
        except BaseException as e:
            if isinstance(e, GeneratorExit):
                self.after(scoped_ctx)
            else:
                self.after_failure(scoped_ctx, e)
            raise
        else:
            self.after(scoped_ctx)

    def open(self, ctx: Context) -> Generator[Any, None, None]:
        if self.effective_mode is Mode.ASYNC:  # subtree sup of own_mode
            msg = (
                f"{type(self).__name__} has ASYNC in its subtree; "
                "cannot run sync. Use aopen / aexecute."
            )
            raise RuntimeError(msg)
        scoped_ctx = self.before(ctx)
        try:
            for child in self._children:
                with closing(child.open(scoped_ctx)) as gen:
                    yield from gen
        except BaseException as e:
            if isinstance(e, GeneratorExit):
                self.after(scoped_ctx)
            else:
                self.after_failure(scoped_ctx, e)
            raise
        else:
            self.after(scoped_ctx)

    def before(self, ctx: Context) -> Context:
        """Set up resources; return scoped context for children."""
        return ctx

    def after(self, ctx: Context) -> None:
        """Clean up after successful execution."""

    def after_failure(self, ctx: Context, error: BaseException) -> None:
        """Clean up after failed execution."""
