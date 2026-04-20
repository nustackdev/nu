"""Nu - the primitive.

Nu is the recursive unit of computation. A Nu is made of Nus.
Both a leaf (`Literal(5)`) and a full app are Nus.

The single evaluator primitive is `open(ctx)` - a raw async generator
over Γ. Body = scope. Pre-first-yield = enter, each `yield` = a value
crossing the bracket, `finally` = exit. Yields 0..N times.

Composition:
    a >> b  = sequential - forward each child's stream in order
    a | b   = parallel   - interleave children's streams

Algebraic annotations on Nu (class-level):
    comm    = children commute (⟦⟧ invariant under reorder)
    indep   = children footprint-disjoint on writes
    assoc   = safe to re-associate nested Nus of the same kind

`can_parallelize()` returns `self.comm and self.indep`. Evaluator uses
this and only this to choose the pump (interleave vs sequential).

Hierarchy:
    Nu[T_co]                - base: runs children sequentially by default
    ├── NuIndepComm[T_co]   - parallel-capable composite (what `|` builds)
    ├── LValue[T_co]        - addressable location (internal)
    │   └── Ref[T_co]       - typed pointer (see ref.py)
    └── RValue[T_co]        - evaluable expression (internal)
        ├── Literal[T_co]   - literal data (see literal.py)
        └── Op[T_co]        - operation (see op.py)
"""

from __future__ import annotations

import asyncio
from abc import ABC
from contextlib import aclosing
from typing import TYPE_CHECKING, Any, ClassVar, Generic

from nu.tree.node import _Node

from .type_vars import T_co


if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from ..context import Context


__all__ = [
    "LValue",
    "Nu",
    "NuIndepComm",
    "RValue",
]


_DONE = object()


class Nu(_Node["Nu"], Generic[T_co]):  # noqa: UP046
    """The primitive. Recursive unit of computation.

    Default `open`: runs children sequentially, forwards their yields.
    Subclasses override `open` for domain semantics.
    `Nu()` with no children is the identity (algebra's `0`).
    """

    # Algebraic annotations. Base defaults: assoc holds (re-grouping is safe
    # for the default sequential pump); comm and indep require declaration.
    comm: ClassVar[bool] = False
    indep: ClassVar[bool] = False
    assoc: ClassVar[bool] = True

    def can_parallelize(self) -> bool:
        """Licenses the interleaving pump. comm ∧ indep."""
        return self.comm and self.indep

    async def open(self, ctx: Context) -> AsyncGenerator[T_co, None]:
        """Run this Nu as a scope. Yields 0..N values.

        Default: dispatch by `can_parallelize()`.
        - True  -> interleave children's streams.
        - False -> forward each child's stream in order.
        """
        if self.can_parallelize():
            async for v in self._pump_parallel(ctx):
                yield v
        else:
            async for v in self._pump_sequential(ctx):
                yield v

    async def _pump_sequential(self, ctx: Context) -> AsyncGenerator[T_co, None]:
        for child in self._children:
            async with aclosing(child.open(ctx)) as gen:
                async for v in gen:
                    yield v

    async def _pump_parallel(self, ctx: Context) -> AsyncGenerator[T_co, None]:
        queue: asyncio.Queue[Any] = asyncio.Queue()

        async def pump(child: Nu) -> None:
            try:
                async with aclosing(child.open(ctx)) as gen:
                    async for v in gen:
                        await queue.put(v)
            finally:
                await queue.put(_DONE)

        tasks = [asyncio.create_task(pump(c)) for c in self._children]
        remaining = len(tasks)
        try:
            while remaining > 0:
                v = await queue.get()
                if v is _DONE:
                    remaining -= 1
                else:
                    yield v
        finally:
            for t in tasks:
                if not t.done():
                    t.cancel()
            for t in tasks:
                try:
                    await t
                except (asyncio.CancelledError, Exception):
                    pass

    # --- consumption helpers (sugar over open) ---

    async def execute(self, ctx: Context | None = None) -> None:
        """Drain. Yields are discarded. Empty Context if none passed."""
        ctx = self._default_ctx(ctx)
        async with aclosing(self.open(ctx)) as gen:
            async for _ in gen:
                pass

    async def drain(self, ctx: Context | None = None) -> None:
        """Alias for execute."""
        await self.execute(ctx)

    async def first(self, ctx: Context | None = None) -> Any:
        """Take the first yield, close the rest."""
        ctx = self._default_ctx(ctx)
        async with aclosing(self.open(ctx)) as gen:
            async for v in gen:
                return v
        msg = "nu yielded no values"
        raise RuntimeError(msg)

    async def last(self, ctx: Context | None = None) -> Any:
        """Drain, return last yield."""
        ctx = self._default_ctx(ctx)
        found = False
        val: Any = None
        async with aclosing(self.open(ctx)) as gen:
            async for v in gen:
                val = v
                found = True
        if not found:
            msg = "nu yielded no values"
            raise RuntimeError(msg)
        return val

    async def collect(self, ctx: Context | None = None) -> list[Any]:
        """Drain into a list."""
        ctx = self._default_ctx(ctx)
        out: list[Any] = []
        async with aclosing(self.open(ctx)) as gen:
            async for v in gen:
                out.append(v)
        return out

    @staticmethod
    def _default_ctx(ctx: Context | None) -> Context:
        if ctx is not None:
            return ctx
        from ..context import Context as _Ctx

        return _Ctx()

    # --- composition operators ---

    def __or__(self, other: object) -> Nu:
        """`a | b` -> parallel composition (NuIndepComm).

        Flattens when chained: `a | b | c` produces one NuIndepComm
        with three children.
        """
        if not isinstance(other, Nu):
            return NotImplemented  # type: ignore[return-value]
        if type(self) is NuIndepComm:
            return NuIndepComm(*self._children, other)
        return NuIndepComm(self, other)

    def __rshift__(self, other: object) -> Nu:
        """`a >> b` -> sequential composition (plain Nu).

        Flattens when chained: `a >> b >> c` produces one Nu with three
        children.
        """
        if not isinstance(other, Nu):
            return NotImplemented  # type: ignore[return-value]
        if type(self) is Nu:
            return Nu(*self._children, other)
        return Nu(self, other)


class NuIndepComm(Nu[T_co]):
    """Parallel-capable composite. Instantiated by `|`.

    Children run concurrently under the interleaving pump. Algebra
    annotations flipped to license it.
    """

    comm: ClassVar[bool] = True
    indep: ClassVar[bool] = True
    assoc: ClassVar[bool] = True


class LValue(Nu[T_co], ABC):
    """Addressable location. Internal base for Ref."""


class RValue(Nu[T_co], ABC):
    """Evaluable expression. Internal base for Literal and Op."""
