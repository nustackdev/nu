"""Sentinel interfaces - SentinelI, EmptyI, InvalidI."""

from __future__ import annotations

from nu.terms import EMPTY, INVALID, Empty, Interface, Invalid, Sentinel, TypedNu


__all__ = [
    "EmptyI",
    "InvalidI",
    "SentinelI",
]


class SentinelI[T: Sentinel](Interface, TypedNu[T]):
    """Base for sentinel interfaces (Empty, Invalid)."""


class EmptyI(SentinelI[Empty]):
    """Empty interface - represents absence of a value."""

    def __init__(self) -> None:
        super().__init__(EMPTY)


class InvalidI(SentinelI[Invalid]):
    """Invalid interface - represents invalid/undefined operations."""

    def __init__(self) -> None:
        super().__init__(INVALID)
