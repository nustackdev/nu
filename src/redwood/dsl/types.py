"""Core type system for DSL.

This module defines special values (Empty, NaN) and type aliases used throughout
the DSL evaluation system.
"""

from __future__ import annotations

from enum import Enum, auto
from typing import TypeVar, Union


__all__ = [
    "Empty",
    "NaN",
    "SpecialValue",
    "TermResult",
    "is_empty",
    "is_nan",
    "is_special",
    "propagate_special",
]


class SpecialValue(Enum):
    """Special sentinel values for DSL evaluation.

    - EMPTY: Path/value doesn't exist in tree
    - NAN: Operation not applicable (e.g., Empty > 15, type mismatch during operation)

    Examples:
        >>> User.missing_field.get()  # Returns EMPTY
        >>> (Empty > 15)  # Returns NAN - can't compare non-existent value
        >>> "text" / 0  # Returns NAN - invalid operation
    """

    EMPTY = auto()
    NAN = auto()

    def __repr__(self) -> str:
        """Return clean representation."""
        return f"SpecialValue.{self.name}"


# Convenient constants
Empty = SpecialValue.EMPTY
NaN = SpecialValue.NAN

T = TypeVar("T")
TermResult = Union[T, SpecialValue]
"""Type alias for term evaluation results.

Can be an actual value of type T, or a special value (Empty/NaN).
"""


def is_empty(value: TermResult) -> bool:
    """Check if value is Empty.

    Args:
        value: Value to check

    Returns:
        True if value is SpecialValue.EMPTY
    """
    return value is SpecialValue.EMPTY


def is_nan(value: TermResult) -> bool:
    """Check if value is NaN.

    Args:
        value: Value to check

    Returns:
        True if value is SpecialValue.NAN
    """
    return value is SpecialValue.NAN


def is_special(value: TermResult) -> bool:
    """Check if value is any special value (Empty or NaN).

    Args:
        value: Value to check

    Returns:
        True if value is a SpecialValue
    """
    return isinstance(value, SpecialValue)


def propagate_special(*values: TermResult) -> SpecialValue | None:
    """Propagate special values through operations.

    Rules:
    1. Any NaN → NaN (NaN is contagious)
    2. Any Empty (no NaN present) → NaN (operation not applicable on missing data)
    3. All normal values → None (continue with operation)

    Args:
        *values: Values to check for special value propagation

    Returns:
        NaN if any value is special, None if all values are normal

    Examples:
        >>> propagate_special(10, 20, 30)  # None - all normal
        >>> propagate_special(10, Empty, 30)  # NaN - has Empty
        >>> propagate_special(10, NaN, 30)  # NaN - has NaN
        >>> propagate_special(Empty, NaN)  # NaN - NaN takes precedence
    """
    # NaN propagates first (highest priority)
    for val in values:
        if is_nan(val):
            return NaN

    # Empty converts to NaN for operations
    for val in values:
        if is_empty(val):
            return NaN

    # All normal values
    return None
