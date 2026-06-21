"""Sentinel interfaces - SentinelForm, EmptyForm, InvalidForm."""

from __future__ import annotations

from nu2.lang import EMPTY, INVALID, Empty, Form, Invalid, Sentinel, TypedNu


__all__ = [
    "EmptyForm",
    "InvalidForm",
    "SentinelForm",
]


class SentinelForm[T: Sentinel](Form, TypedNu[T]):
    """Base for sentinel interfaces (Empty, Invalid)."""


class EmptyForm(SentinelForm[Empty]):
    """Empty interface - represents absence of a value."""

    def __init__(self) -> None:
        super().__init__(EMPTY)


class InvalidForm(SentinelForm[Invalid]):
    """Invalid interface - represents invalid/undefined interactions."""

    def __init__(self) -> None:
        super().__init__(INVALID)
