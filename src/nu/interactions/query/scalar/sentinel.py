"""Sentinel check ops.

IsEmpty, IsInvalid, NotEmpty, NotInvalid

These are inspections, not computations. They need to see sentinels to
answer the question, so they cannot use NAryScalar (which short-circuits
on sentinels before `apply`). Instead they are plain Query[bool] subclasses
that override `arun` / `run` and take the child's first yield directly.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from nu.terms import Mode, Query, is_empty, is_invalid


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

    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def __init__(self, operand: Nu) -> None:
        super().__init__(operand)

    def run(self, ctx: Context) -> bool:
        return is_empty(self._children[0].first(ctx))


class NotEmpty(Query[bool]):
    """Check if operand is NOT Empty sentinel."""

    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def __init__(self, operand: Nu) -> None:
        super().__init__(operand)

    def run(self, ctx: Context) -> bool:
        return not is_empty(self._children[0].first(ctx))


class IsInvalid(Query[bool]):
    """Check if operand is Invalid sentinel."""

    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def __init__(self, operand: Nu) -> None:
        super().__init__(operand)

    def run(self, ctx: Context) -> bool:
        return is_invalid(self._children[0].first(ctx))


class NotInvalid(Query[bool]):
    """Check if operand is NOT Invalid sentinel."""

    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def __init__(self, operand: Nu) -> None:
        super().__init__(operand)

    def run(self, ctx: Context) -> bool:
        return not is_invalid(self._children[0].first(ctx))
