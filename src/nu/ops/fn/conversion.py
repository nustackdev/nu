"""Type conversions — Value-returning factories over op Ops.

ToInt, ToFloat, ToBool, ToStr, ToBytes (primitives)
ToList, ToSet (collections)
"""

from __future__ import annotations

from nu.ops.builtins.conversion import (
    ToBoolOp,
    ToBytesOp,
    ToFloatOp,
    ToIntOp,
    ToListOp,
    ToSetOp,
    ToStrOp,
)
from nu.interfaces import BoolI, BytesI, FloatI, IntI, ListI, SetI, StrI


__all__ = [
    "ToBool",
    "ToBytes",
    "ToFloat",
    "ToInt",
    "ToList",
    "ToSet",
    "ToStr",
]


def ToInt(obj: object) -> IntI:  # noqa: N802
    """Convert to integer."""
    return IntI(ToIntOp(obj))


def ToFloat(obj: object) -> FloatI:  # noqa: N802
    """Convert to float."""
    return FloatI(ToFloatOp(obj))


def ToBool(obj: object) -> BoolI:  # noqa: N802
    """Convert to boolean."""
    return BoolI(ToBoolOp(obj))


def ToStr(obj: object) -> StrI:  # noqa: N802
    """Convert to string."""
    return StrI(ToStrOp(obj))


def ToBytes(obj: object, encoding: str = "utf-8") -> BytesI:  # noqa: N802
    """Convert to bytes."""
    return BytesI(ToBytesOp(obj, encoding))


def ToList(iterable: object) -> ListI:  # noqa: N802
    """Materialize iterable to list."""
    return ListI(ToListOp(iterable))


def ToSet(iterable: object) -> SetI:  # noqa: N802
    """Materialize iterable to set."""
    return SetI(ToSetOp(iterable))
