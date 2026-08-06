"""Sentinel interfaces - SentinelForm, EmptyForm, InvalidForm."""

from __future__ import annotations

from typing import Generic, TypeVar

from nu.lang import EMPTY, INVALID, Empty, Form, Invalid, Sentinel, TypedNu


__all__ = [
    "EmptyForm",
    "InvalidForm",
    "SentinelForm",
]


T = TypeVar("T", bound="Sentinel")


class SentinelForm(Form, TypedNu[T], Generic[T]):
    """Base for sentinel interfaces (Empty, Invalid)."""


class EmptyForm(SentinelForm[Empty]):
    """Empty interface - represents absence of a value."""

    def __init__(self) -> None:
        super().__init__(EMPTY)


class InvalidForm(SentinelForm[Invalid]):
    """Invalid interface - represents invalid/undefined interactions."""

    def __init__(self) -> None:
        super().__init__(INVALID)
