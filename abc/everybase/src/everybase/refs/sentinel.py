"""Sentinel ref bases for special values.

SentinelRefBase - Base for all sentinel types
EmptyRefBase - Represents absence of a value
InvalidRefBase - Represents invalid/undefined operations
"""

from __future__ import annotations

from abc import ABC

from .base import RefBase


__all__ = [
    "EmptyRefBase",
    "InvalidRefBase",
    "SentinelRefBase",
]


class SentinelRefBase(RefBase[None], ABC):
    """Base for sentinel refs (Empty, Invalid).

    Sentinels represent special values indicating absence or invalidity.
    """

    pass


class EmptyRefBase(SentinelRefBase, ABC):
    """Abstract base for Empty refs.

    Represents absence of a value, distinct from None.
    Key properties:
    - is_empty() always returns True
    - or_default(x) always returns x
    """

    pass


class InvalidRefBase(SentinelRefBase, ABC):
    """Abstract base for Invalid refs.

    Represents invalid/undefined operations.
    Key properties:
    - Operations with Invalid propagate Invalid
    - is_invalid() always returns True
    """

    pass
