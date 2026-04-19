"""Evaluation helpers.

Six module-level functions over `Nu.open`. Not methods.

- `execute(nu, ctx) -> None`  drain, discard yields. Algebra-faithful: the
                              algebraic output is Γ', not values.
- `drain(nu, ctx) -> None`    alias for execute.
- `first(nu, ctx) -> Any`     first yield; close the rest.
- `last(nu, ctx) -> Any`      drain; return last yield.
- `collect(nu, ctx) -> list`  drain into a list.
- `fetch(ref, ctx) -> Any`    Ref-specialized first; yields fetched value.

All wrap `aclosing(nu.open(ctx))` for structured cleanup on consumer exit.
"""

from __future__ import annotations

from contextlib import aclosing
from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    from .context import Context
    from .terms import Nu, Ref


__all__ = [
    "collect",
    "drain",
    "execute",
    "fetch",
    "first",
    "last",
]


async def execute(nu: Nu, ctx: Context) -> None:
    """Drain the Nu's stream. Yields are discarded. Returns None."""
    async with aclosing(nu.open(ctx)) as gen:
        async for _ in gen:
            pass


async def drain(nu: Nu, ctx: Context) -> None:
    """Alias for execute."""
    await execute(nu, ctx)


async def first(nu: Nu, ctx: Context) -> Any:
    """Take the first yield, close the rest."""
    async with aclosing(nu.open(ctx)) as gen:
        async for v in gen:
            return v
    msg = "nu yielded no values"
    raise RuntimeError(msg)


async def last(nu: Nu, ctx: Context) -> Any:
    """Drain and return the last yield."""
    found = False
    val: Any = None
    async with aclosing(nu.open(ctx)) as gen:
        async for v in gen:
            val = v
            found = True
    if not found:
        msg = "nu yielded no values"
        raise RuntimeError(msg)
    return val


async def collect(nu: Nu, ctx: Context) -> list[Any]:
    """Drain into a list."""
    out: list[Any] = []
    async with aclosing(nu.open(ctx)) as gen:
        async for v in gen:
            out.append(v)
    return out


async def fetch(ref: Ref, ctx: Context) -> Any:
    """Ref-specialized first. Yields the resolved value."""
    return await first(ref, ctx)
