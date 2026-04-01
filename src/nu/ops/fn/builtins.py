"""Builtin equivalents — Value-returning factories over morphism Ops.

Len -> IntValue
Contains -> BoolValue
"""

from __future__ import annotations

from nu.ops import ContainsOp, LenOp
from nu.interfaces.values import BoolValue, IntValue


__all__ = [
    "Contains",
    "Len",
]


def Len(obj: object) -> IntValue:  # noqa: N802
    """Get length of a sized object. Like Python's ``len()``."""
    return IntValue(LenOp(obj))


def Contains(collection: object, item: object) -> BoolValue:  # noqa: N802
    """Check if item is in collection. Like Python's ``in`` operator."""
    return BoolValue(ContainsOp(collection, item))
