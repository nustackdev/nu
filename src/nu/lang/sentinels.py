"""Sentinels - EMPTY and UNSET.

EMPTY is the one "no value" sentinel: no value here, either missing or
derived from missing. It originates at Ref resolution (the address resolves
to nothing) and flows from there like NULL in SQL: unknown flows through
expressions and never passes a condition.

- Queries propagate it. Any EMPTY operand gives EMPTY, without raising.
- Conditions read it as false. A branch, loop, filter or ``And`` / ``Or``
  treats EMPTY like any falsy value, without poisoning the rest.
- Writes refuse it. Storing EMPTY into a Ref or fabric raises; absence is
  made by erasing, never by writing.
- Real errors stay errors. A wrong type or a bad call raises as in Python.

The checks that observe EMPTY (``IsEmpty``, ``exists()``, ``fallback()``)
take it as an ordinary input and yield a real answer. In a Stream, EMPTY is
just one yielded value; the stream consumer decides what it means per element.
"""

from __future__ import annotations

from typing import TypeGuard


__all__ = [
    "EMPTY",
    "UNSET",
    "Empty",
    "Sentinel",
    "Unset",
    "is_empty",
    "is_sentinel",
]


class Sentinel:
    """Base for special values that stand in for a value that is not there."""


class Empty(Sentinel):
    """No value here, either missing or derived from missing. Distinct from None."""

    def __repr__(self) -> str:
        return "<EMPTY>"

    def __bool__(self) -> bool:
        return False

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Empty)

    def __hash__(self) -> int:
        return hash(type(self).__name__)


class Unset(Sentinel):
    """Absence marker: an argument not provided, or a value not yet set.

    Distinct from EMPTY: UNSET never flows as a value through the engine and
    takes no part in Query propagation. Callers test ``is UNSET`` explicitly -
    e.g. an optional ``initial`` for a fold, or "no previous item yet" loop
    state in a lens.
    """

    def __repr__(self) -> str:
        return "<UNSET>"


EMPTY: Empty = Empty()
UNSET: Unset = Unset()


def is_empty(value: object) -> TypeGuard[Empty]:
    """True if ``value`` is the EMPTY sentinel."""
    return isinstance(value, Empty)


def is_sentinel(value: object) -> TypeGuard[Sentinel]:
    """True if ``value`` is any Sentinel."""
    return isinstance(value, Sentinel)
