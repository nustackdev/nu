"""Special sentinel values for ABC modules."""

from __future__ import annotations

from typing import TypeGuard


__all__ = [
    "EMPTY",
    "NAN",
    "Empty",
    "NaN",
    "Sentinel",
    "is_empty",
    "is_nan",
    "is_special",
    "propagate_special",
]


class Sentinel:
    """Sentinel values for semantics evaluation.

    - Empty: Value doesn't exist
    - NaN: Operation not applicable
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


class NaN(Sentinel):
    """Sentinel for invalid operations."""

    def __repr__(self) -> str:
        """String representation for debugging."""
        return "<NaN>"

    def __str__(self) -> str:
        """String representation for display."""
        return "NaN"

    def __bool__(self) -> bool:
        """Boolean evaluation, always False."""
        return False

    def __eq__(self, other: object) -> bool:
        return isinstance(other, NaN)

    def __hash__(self) -> int:
        return hash("NaN")


# Singleton instances
EMPTY = Empty()
NAN = NaN()


def is_empty(value: object) -> TypeGuard[Empty]:
    """Check if value is Empty sentinel."""
    return isinstance(value, Empty)


def is_nan(value: object) -> TypeGuard[NaN]:
    """Check if value is NaN sentinel."""
    return isinstance(value, NaN)


def is_special(value: object) -> TypeGuard[Sentinel]:
    """Check if value is any special sentinel."""
    return isinstance(value, Sentinel)


def propagate_special(*values: object) -> NaN | Empty | None:
    """Propagate special values through operations.

    Rules:
    1. Any NaN → NaN
    2. Any Empty → NaN
    3. All normal → None

    Returns:
        NaN if any special value present, None otherwise
    """
    for val in values:
        if is_nan(val):
            return NAN

    for val in values:
        if is_empty(val):
            return NAN

    return None
