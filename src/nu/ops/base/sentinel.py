"""Sentinel check ops.

IsEmptyOp, IsInvalidOp, NotEmptyOp, NotInvalidOp

These are inspections, not computations. They need to see sentinels
to answer the question, so they bypass NAryOp's sentinel propagation
by overriding open() directly.
"""

from __future__ import annotations

from contextlib import aclosing
from typing import TYPE_CHECKING, Any

from nu.terms import Op, is_empty, is_invalid


if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from nu.context import Context
    from nu.terms import Nu


__all__ = [
    "IsEmptyOp",
    "IsInvalidOp",
    "NotEmptyOp",
    "NotInvalidOp",
]


async def _drain_last(child: Nu, ctx: Context) -> Any:
    """Drain a child's stream and return its last yielded value."""
    val: Any = None
    async with aclosing(child.open(ctx)) as gen:
        async for v in gen:
            val = v
    return val


class IsEmptyOp(Op[bool]):
    """Check if operand is Empty sentinel."""

    def __init__(self, operand: Nu) -> None:
        super().__init__(operand)

    async def open(self, ctx: Context) -> AsyncGenerator[bool, None]:
        yield is_empty(await _drain_last(self.children[0], ctx))


class NotEmptyOp(Op[bool]):
    """Check if operand is NOT Empty sentinel."""

    def __init__(self, operand: Nu) -> None:
        super().__init__(operand)

    async def open(self, ctx: Context) -> AsyncGenerator[bool, None]:
        yield not is_empty(await _drain_last(self.children[0], ctx))


class IsInvalidOp(Op[bool]):
    """Check if operand is Invalid sentinel."""

    def __init__(self, operand: Nu) -> None:
        super().__init__(operand)

    async def open(self, ctx: Context) -> AsyncGenerator[bool, None]:
        yield is_invalid(await _drain_last(self.children[0], ctx))


class NotInvalidOp(Op[bool]):
    """Check if operand is NOT Invalid sentinel."""

    def __init__(self, operand: Nu) -> None:
        super().__init__(operand)

    async def open(self, ctx: Context) -> AsyncGenerator[bool, None]:
        yield not is_invalid(await _drain_last(self.children[0], ctx))
