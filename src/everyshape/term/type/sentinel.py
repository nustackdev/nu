"""Sentinel types for Term expressions.

This module provides sentinel types for special values:
- SentinelType - Base for sentinel types
- EmptyType - Represents absence of a value
- NAType - Represents invalid/undefined operations
"""

from __future__ import annotations

from .type import Type


__all__ = [
    "EmptyType",
    "NAType",
    "SentinelType",
]


class SentinelType(Type[None]):
    """Base for sentinel types (EmptyType, NAType).

    Sentinels represent special values that indicate absence or invalidity.
    """

    pass


class EmptyType(SentinelType):
    """Empty type - represents absence of a value.

    EmptyType represents the absence of a value, distinct from None.
    It can be used as a sentinel for missing data.

    Key properties:
    - is_empty() always returns True
    - or_default(x) always returns x

    Example:
        >>> empty = EmptyType()
        >>> empty.is_empty()  # Always BoolType(True)
        >>> empty.or_default(42)  # Returns 42
    """

    def __init__(self) -> None:
        """Initialize empty type."""
        super().__init__(None)

    def execute(self, context: object) -> None:
        """Execute returns None for empty values."""
        return None


class NAType(SentinelType):
    """Not Applicable type - represents invalid/undefined operations.

    NAType represents an invalid or not-applicable result.
    Operations on NA propagate NA.

    Key properties:
    - Represents "not applicable" (N/A), not "not a number"
    - Operations with NA return NA
    - is_na() always returns True

    Example:
        >>> na = NAType()
        >>> na.is_na()  # Always BoolType(True)
    """

    def __init__(self) -> None:
        """Initialize NA type."""
        super().__init__(None)

    def execute(self, context: object) -> None:
        """Execute returns None for NA values."""
        return None
