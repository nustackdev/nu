"""Type conversions — Value-returning factories over morphism Ops.

ToInt, ToFloat, ToBool, ToStr, ToBytes (primitives)
ToList, ToSet (collections)
"""

from __future__ import annotations

from ..morphisms.builtins.conversion import (
    ToBoolOp,
    ToBytesOp,
    ToFloatOp,
    ToIntOp,
    ToListOp,
    ToSetOp,
    ToStrOp,
)
from ..values import BoolValue, BytesValue, FloatValue, IntValue, ListValue, SetValue, StrValue


__all__ = [
    "ToBool",
    "ToBytes",
    "ToFloat",
    "ToInt",
    "ToList",
    "ToSet",
    "ToStr",
]


def ToInt(obj: object) -> IntValue:  # noqa: N802
    """Convert to integer."""
    return IntValue(ToIntOp(obj))


def ToFloat(obj: object) -> FloatValue:  # noqa: N802
    """Convert to float."""
    return FloatValue(ToFloatOp(obj))


def ToBool(obj: object) -> BoolValue:  # noqa: N802
    """Convert to boolean."""
    return BoolValue(ToBoolOp(obj))


def ToStr(obj: object) -> StrValue:  # noqa: N802
    """Convert to string."""
    return StrValue(ToStrOp(obj))


def ToBytes(obj: object, encoding: str = "utf-8") -> BytesValue:  # noqa: N802
    """Convert to bytes."""
    return BytesValue(ToBytesOp(obj, encoding))


def ToList(iterable: object) -> ListValue:  # noqa: N802
    """Materialize iterable to list."""
    return ListValue(ToListOp(iterable))


def ToSet(iterable: object) -> SetValue:  # noqa: N802
    """Materialize iterable to set."""
    return SetValue(ToSetOp(iterable))
