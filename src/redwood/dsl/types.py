"""Special value types for DSL evaluation.

Defines Empty and NaN sentinel values for graceful error handling:
- Empty: Path/value doesn't exist in tree
- NaN: Operation not applicable (type mismatch, invalid operation)
"""

from enum import Enum, auto


class SpecialValue(Enum):
    """Sentinel values for DSL evaluation results.

    - EMPTY: Path or value doesn't exist in tree
    - NAN: Operation not applicable or invalid

    Examples:
        >>> User.missing_field.get()  # Returns EMPTY
        >>> Empty > 15  # Returns NAN (can't compare non-existent value)
        >>> "text" / 2  # Returns NAN (invalid operation)
    """

    EMPTY = auto()
    NAN = auto()

    def __repr__(self) -> str:
        return f"SpecialValue.{self.name}"


# Convenient constants
Empty = SpecialValue.EMPTY
NaN = SpecialValue.NAN


def is_empty(value: object) -> bool:
    """Check if value is Empty.

    Args:
        value: Value to check

    Returns:
        True if value is SpecialValue.EMPTY
    """
    return value is SpecialValue.EMPTY


def is_nan(value: object) -> bool:
    """Check if value is NaN.

    Args:
        value: Value to check

    Returns:
        True if value is SpecialValue.NAN
    """
    return value is SpecialValue.NAN


def is_special(value: object) -> bool:
    """Check if value is any special value (Empty or NaN).

    Args:
        value: Value to check

    Returns:
        True if value is a SpecialValue
    """
    return isinstance(value, SpecialValue)


def propagate_special(*values: object) -> SpecialValue | None:
    """Propagate special values through operations.

    Rules:
    1. Any NaN → NaN (NaN is contagious, highest priority)
    2. Any Empty (no NaN present) → NaN (operation not applicable)
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
