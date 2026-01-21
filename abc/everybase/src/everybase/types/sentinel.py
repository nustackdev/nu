"""Sentinel types for Term expressions.

This module provides sentinel types for special values:
- SentinelType - Base for sentinel types
- EmptyType - Represents absence of a value
- InvalidType - Represents invalid/undefined operations
"""

from __future__ import annotations

from everybase.bases import BaseType


__all__ = [
    "EmptyType",
    "InvalidType",
    "SentinelType",
]


class SentinelType(BaseType[None]):
    """Base for sentinel types (EmptyType, InvalidType).

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
        """Init."""
        """Initialize empty type."""
        super().__init__(None)

    def execute(self, context: object) -> None:
        """Execute."""
        """Execute returns None for empty values."""
        return None


class InvalidType(SentinelType):
    """Invalid type - represents invalid/undefined operations.

    InvalidType represents an invalid or not-applicable result.
    Operations on INVALID propagate INVALID.

    Key properties:
    - Represents "not applicable" (N/A)
    - Operations with INVALID return INVALID
    - is_invalid() always returns True

    Example:
        >>> na = InvalidType()
        >>> na.is_invalid()  # Always BoolType(True)
    """

    def __init__(self) -> None:
        """Init."""
        """Initialize INVALID type."""
        super().__init__(None)

    def execute(self, context: object) -> None:
        """Execute."""
        """Execute returns None for INVALID values."""
        return None
