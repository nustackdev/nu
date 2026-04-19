"""Sentinel interfaces - SentinelI, EmptyI, InvalidI."""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.interface import Interface, TypedNu
from nu.terms import EMPTY, INVALID, Empty, Invalid, Sentinel


if TYPE_CHECKING:
    from nu.context import Context


__all__ = [
    "EmptyI",
    "InvalidI",
    "SentinelI",
]


class SentinelI[T: Sentinel](Interface, TypedNu[T]):
    """Base for sentinel interfaces (Empty, Invalid)."""

    pass


class EmptyI(SentinelI[Empty]):
    """Empty interface - represents absence of a value."""

    def __init__(self) -> None:
        super().__init__(EMPTY)

    # TODO task-079: depends on TypedNu port (other bucket). When TypedNu
    # switches to open() as async generator, replace this with a one-yield
    # override (or drop entirely if TypedNu already wraps the literal child).
    async def execute(self, ctx: Context) -> Empty:
        return EMPTY


class InvalidI(SentinelI[Invalid]):
    """Invalid interface - represents invalid/undefined operations."""

    def __init__(self) -> None:
        super().__init__(INVALID)

    # TODO task-079: depends on TypedNu port (other bucket). Same as EmptyI.
    async def execute(self, ctx: Context) -> Invalid:
        return INVALID
