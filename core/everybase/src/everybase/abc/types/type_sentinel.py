"""Sentinel ref bases for special values.

SentinelType - Base for all sentinel types
EmptyType - Represents absence of a value
InvalidType - Represents invalid/undefined operations
"""

from __future__ import annotations

from everybase.core import Empty, Invalid, Sentinel

from .base import TypeBase


__all__ = [
    "EmptyType",
    "InvalidType",
    "SentinelType",
]


class SentinelType[T: Sentinel](TypeBase[T]):
    """Base for sentinel refs (Empty, Invalid).

    Sentinels represent special values indicating absence or invalidity.
    """

    pass


class EmptyType(SentinelType[Empty]):
    """Abstract base for Empty refs.

    Represents absence of a value, distinct from None.
    Key properties:
    - is_empty() always returns True
    - or_default(x) always returns x
    """

    pass


class InvalidType(SentinelType[Invalid]):
    """Abstract base for Invalid refs.

    Represents invalid/undefined operations.
    Key properties:
    - Operations with Invalid propagate Invalid
    - is_invalid() always returns True
    """

    pass
