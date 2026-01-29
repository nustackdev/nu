"""Python memory sentinel refs.

SentinelRef, EmptyRef, InvalidRef = PyRefBase + SentinelRefBase variants
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from everyabc import EMPTY, INVALID, Sentinel
from everybase.refs import EmptyRefBase, InvalidRefBase, SentinelRefBase

from .base import PyRefBase


if TYPE_CHECKING:
    from everyabc import Context


__all__ = [
    "EmptyRef",
    "InvalidRef",
    "SentinelRef",
]


class SentinelRef(PyRefBase[None], SentinelRefBase):
    """Concrete sentinel ref for Python memory storage."""

    pass


class EmptyRef(PyRefBase[None], EmptyRefBase):
    """Concrete empty ref for Python memory storage.

    Represents absence of a value.
    """

    def __init__(self) -> None:
        """Initialize empty ref."""
        super().__init__(None)

    def get(self, ctx: Context) -> Sentinel:
        """Get returns EMPTY sentinel."""
        return EMPTY


class InvalidRef(PyRefBase[None], InvalidRefBase):
    """Concrete invalid ref for Python memory storage.

    Represents invalid/undefined operations.
    """

    def __init__(self) -> None:
        """Initialize invalid ref."""
        super().__init__(None)

    def get(self, ctx: Context) -> Sentinel:
        """Get returns INVALID sentinel."""
        return INVALID
