"""Sentinel check ops.

IsEmptyOp, IsInvalidOp, NotEmptyOp, NotInvalidOp

These are inspections, not computations. They need to see sentinels
to answer the question, so they bypass NAryOp's sentinel propagation
by overriding execute() directly.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.terms import Calculation, is_empty, is_invalid


if TYPE_CHECKING:
    from nu.context import Context
    from nu.terms import Nu


__all__ = [
    "IsEmptyOp",
    "IsInvalidOp",
    "NotEmptyOp",
    "NotInvalidOp",
]


class IsEmptyOp(Calculation[bool]):
    """Check if operand is Empty sentinel."""

    def __init__(self, operand: Nu) -> None:
        super().__init__(operand)

    async def execute(self, ctx: Context) -> bool:
        value = await self.children[0].execute(ctx)
        return is_empty(value)


class NotEmptyOp(Calculation[bool]):
    """Check if operand is NOT Empty sentinel."""

    def __init__(self, operand: Nu) -> None:
        super().__init__(operand)

    async def execute(self, ctx: Context) -> bool:
        value = await self.children[0].execute(ctx)
        return not is_empty(value)


class IsInvalidOp(Calculation[bool]):
    """Check if operand is Invalid sentinel."""

    def __init__(self, operand: Nu) -> None:
        super().__init__(operand)

    async def execute(self, ctx: Context) -> bool:
        value = await self.children[0].execute(ctx)
        return is_invalid(value)


class NotInvalidOp(Calculation[bool]):
    """Check if operand is NOT Invalid sentinel."""

    def __init__(self, operand: Nu) -> None:
        super().__init__(operand)

    async def execute(self, ctx: Context) -> bool:
        value = await self.children[0].execute(ctx)
        return not is_invalid(value)
