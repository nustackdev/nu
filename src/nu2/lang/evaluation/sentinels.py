"""Sentinels - EMPTY and INVALID.

EMPTY originates only at Ref resolution (the address resolves to nothing).
INVALID originates when an operation is applied to an EMPTY operand. If any
operand of a Query is EMPTY or INVALID, the Query returns INVALID - sentinels
collapse to INVALID upward through Query chains.

Sentinel-check ops (IsEmpty, IsInvalid) bypass propagation: they accept any
value and return Bool. In a Stream, a sentinel is just one yielded value;
the stream consumer decides what it means per element.
"""

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
]


class Sentinel:
    """Base for special values that propagate through Query chains."""


class Empty(Sentinel):
    """Address resolved, no value present. Distinct from None."""

    def __repr__(self) -> str:
        return "<EMPTY>"

    def __bool__(self) -> bool:
        return False

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Empty)

    def __hash__(self) -> int:
        return hash(type(self).__name__)


class Invalid(Sentinel):
    """Operation not applicable. Cannot produce a meaningful result."""

    def __repr__(self) -> str:
        return "<INVALID>"

    def __bool__(self) -> bool:
        return False

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Invalid)

    def __hash__(self) -> int:
        return hash(type(self).__name__)


EMPTY: Empty = Empty()
INVALID: Invalid = Invalid()


def is_empty(value: object) -> TypeGuard[Empty]:
    """True if ``value`` is the EMPTY sentinel."""
    return isinstance(value, Empty)


def is_invalid(value: object) -> TypeGuard[Invalid]:
    """True if ``value`` is the INVALID sentinel."""
    return isinstance(value, Invalid)


def is_sentinel(value: object) -> TypeGuard[Sentinel]:
    """True if ``value`` is any Sentinel."""
    return isinstance(value, Sentinel)
