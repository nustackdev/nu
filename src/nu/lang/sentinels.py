"""UNSET: the internal "argument not given" marker.

UNSET never flows as a value through a program. The no-value value is NULL,
in ``nu.lang.null``.
"""

from __future__ import annotations

from typing import TypeGuard

from .null import NULL, Null


__all__ = [
    "EMPTY",
    "UNSET",
    "Sentinel",
    "Unset",
    "is_sentinel",
]


class Sentinel:
    """Base for internal marker values."""


class Unset(Sentinel):
    """Absence marker: an argument not provided, or a value not yet set.

    Not NULL: UNSET never flows as a value through the engine. Callers test
    ``is UNSET`` explicitly, e.g. an optional ``initial`` for a fold, or "no
    previous item yet" loop state in a lens.
    """

    def __repr__(self) -> str:
        return "<UNSET>"


UNSET: Unset = Unset()

# Temporary alias while nustd moves to NULL. Do not use in new code.
EMPTY: Null = NULL


def is_sentinel(value: object) -> TypeGuard[Sentinel]:
    """True if ``value`` is any Sentinel."""
    return isinstance(value, Sentinel)
