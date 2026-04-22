"""Sentinel check ops.

IsEmpty, IsInvalid, NotEmpty, NotInvalid

These are inspections, not computations. They need to see sentinels to
answer the question, so they cannot use NAryScalar (which short-circuits
on sentinels before `apply`). Instead they are plain Query[bool] subclasses
that override `run` / `run_sync` and take the child's first yield directly.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.terms import Query, is_empty, is_invalid


if TYPE_CHECKING:
    from nu.context import Context
    from nu.terms import Nu


__all__ = [
    "IsEmpty",
    "IsInvalid",
    "NotEmpty",
    "NotInvalid",
]


class IsEmpty(Query[bool]):
    """Check if operand is Empty sentinel."""

    def __init__(self, operand: Nu) -> None:
        super().__init__(operand)

    async def run(self, ctx: Context) -> bool:
        return is_empty(await self._children[0].first(ctx))

    def run_sync(self, ctx: Context) -> bool:
        return is_empty(self._children[0].first_sync(ctx))


class NotEmpty(Query[bool]):
    """Check if operand is NOT Empty sentinel."""

    def __init__(self, operand: Nu) -> None:
        super().__init__(operand)

    async def run(self, ctx: Context) -> bool:
        return not is_empty(await self._children[0].first(ctx))

    def run_sync(self, ctx: Context) -> bool:
        return not is_empty(self._children[0].first_sync(ctx))


class IsInvalid(Query[bool]):
    """Check if operand is Invalid sentinel."""

    def __init__(self, operand: Nu) -> None:
        super().__init__(operand)

    async def run(self, ctx: Context) -> bool:
        return is_invalid(await self._children[0].first(ctx))

    def run_sync(self, ctx: Context) -> bool:
        return is_invalid(self._children[0].first_sync(ctx))


class NotInvalid(Query[bool]):
    """Check if operand is NOT Invalid sentinel."""

    def __init__(self, operand: Nu) -> None:
        super().__init__(operand)

    async def run(self, ctx: Context) -> bool:
        return not is_invalid(await self._children[0].first(ctx))

    def run_sync(self, ctx: Context) -> bool:
        return not is_invalid(self._children[0].first_sync(ctx))
