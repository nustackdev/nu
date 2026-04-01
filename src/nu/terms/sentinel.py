"""Sentinel -- special values for computation semantics."""

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
    """Base class for special sentinel values."""


class Empty(Sentinel):
    """Value doesn't exist.

    Represents the absence of a value -- distinct from None.
    """

    def __repr__(self) -> str:
        """Return string representation."""
        return "<Empty>"

    def __bool__(self) -> bool:
        """Empty is falsy."""
        return False

    def __eq__(self, other: object) -> bool:
        """Equality by isinstance."""
        return isinstance(other, Empty)

    def __hash__(self) -> int:
        """Hash by class name."""
        return hash(type(self).__name__)


class Invalid(Sentinel):
    """Operation not applicable.

    Represents a computation that cannot produce a meaningful result.
    """

    def __repr__(self) -> str:
        """Return string representation."""
        return "<Invalid>"

    def __bool__(self) -> bool:
        """Invalid is falsy."""
        return False

    def __eq__(self, other: object) -> bool:
        """Equality by isinstance."""
        return isinstance(other, Invalid)

    def __hash__(self) -> int:
        """Hash by class name."""
        return hash(type(self).__name__)


EMPTY: Empty = Empty()
"""Singleton Empty instance."""

INVALID: Invalid = Invalid()
"""Singleton Invalid instance."""


def is_empty(value: object) -> TypeGuard[Empty]:
    """Check if value is Empty."""
    return isinstance(value, Empty)


def is_invalid(value: object) -> TypeGuard[Invalid]:
    """Check if value is Invalid."""
    return isinstance(value, Invalid)


def is_sentinel(value: object) -> TypeGuard[Sentinel]:
    """Check if value is any Sentinel."""
    return isinstance(value, Sentinel)


def propagate_special(*values: object) -> Invalid | Empty | None:
    """Propagate special values through computation.

    If any value is Invalid or Empty, returns INVALID.
    Otherwise returns None (meaning all values are normal).
    """
    for v in values:
        if isinstance(v, (Invalid, Empty)):
            return INVALID
    return None
