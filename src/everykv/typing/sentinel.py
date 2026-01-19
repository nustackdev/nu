"""Special sentinel values for ABC modules."""

from __future__ import annotations

from typing import TypeGuard


__all__ = [
    "EMPTY",
    "INVALID",
    "Empty",
    "Invalid",
    "Sentinel",
    "is_empty",
    "is_invalid",
    "is_sentinel",
    "propagate_special",
]


class Sentinel:
    """Sentinel values for semantics evaluation.

    - Empty: Value doesn't exist
    - Invalid: Operation not applicable
    """

    pass


class Empty(Sentinel):
    """Sentinel for non-existent values."""

    def __repr__(self) -> str:
        """String representation for debugging."""
        return "<Empty>"

    def __str__(self) -> str:
        """String representation for display."""
        return "Empty"

    def __bool__(self) -> bool:
        """Boolean evaluation, always False."""
        return False

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Empty)

    def __hash__(self) -> int:
        return hash("Empty")


class Invalid(Sentinel):
    """Sentinel for invalid operations."""

    def __repr__(self) -> str:
        """String representation for debugging."""
        return "<Invalid>"

    def __str__(self) -> str:
        """String representation for display."""
        return "Invalid"

    def __bool__(self) -> bool:
        """Boolean evaluation, always False."""
        return False

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Invalid)

    def __hash__(self) -> int:
        return hash("Invalid")


# Singleton instances
EMPTY = Empty()
INVALID = Invalid()


def is_empty(value: object) -> TypeGuard[Empty]:
    """Check if value is Empty sentinel."""
    return isinstance(value, Empty)


def is_invalid(value: object) -> TypeGuard[Invalid]:
    """Check if value is Invalid sentinel."""
    return isinstance(value, Invalid)


def is_sentinel(value: object) -> TypeGuard[Sentinel]:
    """Check if value is any special sentinel."""
    return isinstance(value, Sentinel)


def propagate_special(*values: object) -> Invalid | Empty | None:
    """Propagate special values through operations.

    Rules:
    1. Any Invalid → Invalid
    2. Any Empty → Invalid
    3. All normal → None

    Returns:
        Invalid if any special value present, None otherwise
    """
    for val in values:
        if is_invalid(val) or is_empty(val):
            return INVALID

    return None
