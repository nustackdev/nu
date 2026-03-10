"""Concrete sentinel value types for Python memory storage."""

from __future__ import annotations

from typing import TYPE_CHECKING

from everybase.core import EMPTY, INVALID, Empty, Invalid, Sentinel

from ...types import EmptyType, InvalidType, SentinelType
from ..base import ValueBase


if TYPE_CHECKING:
    from everybase.core import Context


class SentinelValue[T](ValueBase[T], SentinelType):
    """Concrete sentinel value for Python memory storage."""

    pass


class EmptyValue(ValueBase[Empty], EmptyType):
    """Concrete empty value — represents absence of a value."""

    def __init__(self) -> None:
        """Initialize empty value."""
        super().__init__(EMPTY)

    async def fetch(self, ctx: Context) -> Sentinel:
        """Get returns EMPTY sentinel."""
        return EMPTY


class InvalidValue(ValueBase[Invalid], InvalidType):
    """Concrete invalid value — represents invalid/undefined operations."""

    def __init__(self) -> None:
        """Initialize invalid value."""
        super().__init__(INVALID)

    async def fetch(self, ctx: Context) -> Sentinel:
        """Get returns INVALID sentinel."""
        return INVALID
