"""Builtin equivalents — Value-returning factories over op Ops.

Len -> IntI
Contains -> BoolI
"""

from __future__ import annotations

from nu.ops import ContainsOp, LenOp
from nu.interfaces import BoolI, IntI


__all__ = [
    "Contains",
    "Len",
]


def Len(obj: object) -> IntI:  # noqa: N802
    """Get length of a sized object. Like Python's ``len()``."""
    return IntI(LenOp(obj))


def Contains(collection: object, item: object) -> BoolI:  # noqa: N802
    """Check if item is in collection. Like Python's ``in`` operator."""
    return BoolI(ContainsOp(collection, item))
