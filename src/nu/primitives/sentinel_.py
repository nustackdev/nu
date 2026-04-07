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

    async def execute(self, ctx: Context) -> Empty:
        return EMPTY


class InvalidI(SentinelI[Invalid]):
    """Invalid interface - represents invalid/undefined operations."""

    def __init__(self) -> None:
        super().__init__(INVALID)

    async def execute(self, ctx: Context) -> Invalid:
        return INVALID
