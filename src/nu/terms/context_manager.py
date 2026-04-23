"""ContextManager - transparent bracket around a body.

One of the four direct Nu kinds:

    Nu
    ├── Ref
    ├── Interaction
    ├── Form
    └── ContextManager    (this module)

Pure structural. No fabric interaction, no computation of its own, no role.
Brackets child evaluation with `before` / `after` / `after_failure` hooks and
forwards children's yields in order. Transparent: the yield shape is whatever
the body produces (0-yield if children are all Commands, N-yield if children
include Queries / Streams).

ContextManager does NOT mix with Command / Query. Effect contributions come
from the body's children, not the bracket itself.
"""

from __future__ import annotations

import inspect
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


_VALID_MODE_PAIRS: frozenset[tuple[Mode, Mode]] = frozenset(
    {
        (Mode.SYNC, Mode.SYNC),
        (Mode.BOTH, Mode.SYNC),
        (Mode.BOTH, Mode.BOTH),
        (Mode.ASYNC, Mode.ASYNC),
    }
)


class ContextManager(Nu, ABC):
    """Brackets children with before/after hooks.

    Hooks:
        before(ctx) -> ctx        enter. return scoped ctx for the body.
        after(ctx)                exit, clean path.
        after_failure(ctx, exc)   exit, exception path.

    `aopen` runs children under the bracket. Early generator close
    (`GeneratorExit`) routes to `after_failure` — partial consumption is
    treated as abort, not commit. A Transaction half-read shouldn't silently
    persist writes the downstream never observed. Only clean fall-through
    (all children drained, no exception) calls `after`.

    Mode enforcement mirrors Interaction / Ref: concrete subclasses declare
    `own_mode` and `func_mode` in their own __dict__; pair must be one of
    (SYNC,SYNC), (BOTH,SYNC), (BOTH,BOTH), (ASYNC,ASYNC).
    """

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        if ABC in cls.__bases__ or inspect.isabstract(cls):
            return
        for name in ("own_mode", "func_mode"):
            if name not in cls.__dict__:
                msg = (
                    f"{cls.__module__}.{cls.__qualname__} must declare "
                    f"`{name}` explicitly (Mode.SYNC, Mode.ASYNC, or Mode.BOTH). "
                    "Inheritance is not enough — explicit is better than implicit."
                )
                raise TypeError(msg)
        pair = (cls.own_mode, cls.func_mode)
        if pair not in _VALID_MODE_PAIRS:
            msg = (
                f"{cls.__module__}.{cls.__qualname__} declares "
                f"own_mode={cls.own_mode.name}, func_mode={cls.func_mode.name}. "
                "Valid pairs: (SYNC,SYNC), (BOTH,SYNC), (BOTH,BOTH), "
                "(ASYNC,ASYNC). See projects/nu/model/programming/modes.md."
            )
            raise TypeError(msg)

    async def aopen(self, ctx: Context) -> AsyncGenerator[Any, None]:
        scoped_ctx = self.before(ctx)
        try:
            for child in self._children:
                async for v in self._adispatch_child(child, scoped_ctx):
                    yield v
        except BaseException as e:
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
