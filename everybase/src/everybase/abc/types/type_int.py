"""Integer ref base combining numeric traits.

IntValue = TypeBase[int] + Numeric + Comparable + Logical + Bitwise

Returns concrete py types (IntValue, FloatValue, BoolValue).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, overload

from ..capabilities import BitwiseBase, ComparableBase, LogicalBase
from .base import TypeBase


if TYPE_CHECKING:
    from everybase.core import Term

    from ..values import BoolValue, FloatValue, IntValue


__all__ = [
    "IntType",
]


class IntType(
    ComparableBase["int | float | IntValue | FloatValue"],
    LogicalBase["bool | int | BoolValue | IntValue", "BoolValue"],
    BitwiseBase["int | IntValue", "IntValue"],
    TypeBase[int],
):
    """Abstract base for integer refs.

    Combines traits and returns concrete py types.
    """

    def _wrap_bitwise_result(self, operand: Term) -> IntValue:
        from ..values import IntValue

        return IntValue(operand)

    def _wrap_logical_result(self, operand: Term) -> BoolValue:
        from ..values import BoolValue

        return BoolValue(operand)

    # =========================================================================
    # ARITHMETIC (with int/float promotion)
    # =========================================================================

    @overload
    def __add__(self, other: int | IntValue) -> IntValue: ...
    @overload
    def __add__(self, other: float | FloatValue) -> FloatValue: ...
    def __add__(self, other: int | float | IntValue | FloatValue) -> IntValue | FloatValue:
        from ..morphisms import AddOp
        from ..values import FloatValue, IntValue

        if isinstance(other, (float, FloatValue)):
            return FloatValue(AddOp(self, other))
        return IntValue(AddOp(self, other))

    @overload
    def __radd__(self, other: int) -> IntValue: ...
    @overload
    def __radd__(self, other: float) -> FloatValue: ...
    def __radd__(self, other: int | float) -> IntValue | FloatValue:
        from ..morphisms import AddOp
        from ..values import FloatValue, IntValue

        if isinstance(other, float):
            return FloatValue(AddOp(other, self))
        return IntValue(AddOp(other, self))

    @overload
    def __sub__(self, other: int | IntValue) -> IntValue: ...
    @overload
    def __sub__(self, other: float | FloatValue) -> FloatValue: ...
    def __sub__(self, other: int | float | IntValue | FloatValue) -> IntValue | FloatValue:
        from ..morphisms import SubOp
        from ..values import FloatValue, IntValue

        if isinstance(other, (float, FloatValue)):
            return FloatValue(SubOp(self, other))
        return IntValue(SubOp(self, other))

    @overload
    def __rsub__(self, other: int) -> IntValue: ...
    @overload
    def __rsub__(self, other: float) -> FloatValue: ...
    def __rsub__(self, other: int | float) -> IntValue | FloatValue:
        from ..morphisms import SubOp
        from ..values import FloatValue, IntValue

        if isinstance(other, float):
            return FloatValue(SubOp(other, self))
        return IntValue(SubOp(other, self))

    @overload
    def __mul__(self, other: int | IntValue) -> IntValue: ...
    @overload
    def __mul__(self, other: float | FloatValue) -> FloatValue: ...
    def __mul__(self, other: int | float | IntValue | FloatValue) -> IntValue | FloatValue:
        from ..morphisms import MulOp
        from ..values import FloatValue, IntValue

        if isinstance(other, (float, FloatValue)):
            return FloatValue(MulOp(self, other))
        return IntValue(MulOp(self, other))

    @overload
    def __rmul__(self, other: int) -> IntValue: ...
    @overload
    def __rmul__(self, other: float) -> FloatValue: ...
    def __rmul__(self, other: int | float) -> IntValue | FloatValue:
        from ..morphisms import MulOp
        from ..values import FloatValue, IntValue

        if isinstance(other, float):
            return FloatValue(MulOp(other, self))
        return IntValue(MulOp(other, self))

    def __truediv__(self, other: int | float | IntValue | FloatValue) -> FloatValue:
        from ..morphisms import DivOp
        from ..values import FloatValue

        return FloatValue(DivOp(self, other))

    def __rtruediv__(self, other: int | float) -> FloatValue:
        from ..morphisms import DivOp
        from ..values import FloatValue

        return FloatValue(DivOp(other, self))

    @overload
    def __floordiv__(self, other: int | IntValue) -> IntValue: ...
    @overload
    def __floordiv__(self, other: float | FloatValue) -> FloatValue: ...
    def __floordiv__(self, other: int | float | IntValue | FloatValue) -> IntValue | FloatValue:
        from ..morphisms import FloorDivOp
        from ..values import FloatValue, IntValue

        if isinstance(other, (float, FloatValue)):
            return FloatValue(FloorDivOp(self, other))
        return IntValue(FloorDivOp(self, other))

    @overload
    def __rfloordiv__(self, other: int) -> IntValue: ...
    @overload
    def __rfloordiv__(self, other: float) -> FloatValue: ...
    def __rfloordiv__(self, other: int | float) -> IntValue | FloatValue:
        from ..morphisms import FloorDivOp
        from ..values import FloatValue, IntValue

        if isinstance(other, float):
            return FloatValue(FloorDivOp(other, self))
        return IntValue(FloorDivOp(other, self))

    @overload
    def __mod__(self, other: int | IntValue) -> IntValue: ...
    @overload
    def __mod__(self, other: float | FloatValue) -> FloatValue: ...
    def __mod__(self, other: int | float | IntValue | FloatValue) -> IntValue | FloatValue:
        from ..morphisms import ModOp
        from ..values import FloatValue, IntValue

        if isinstance(other, (float, FloatValue)):
            return FloatValue(ModOp(self, other))
        return IntValue(ModOp(self, other))

    @overload
    def __rmod__(self, other: int) -> IntValue: ...
    @overload
    def __rmod__(self, other: float) -> FloatValue: ...
    def __rmod__(self, other: int | float) -> IntValue | FloatValue:
        from ..morphisms import ModOp
        from ..values import FloatValue, IntValue

        if isinstance(other, float):
            return FloatValue(ModOp(other, self))
        return IntValue(ModOp(other, self))

    @overload
    def __pow__(self, other: int | IntValue) -> IntValue: ...
    @overload
    def __pow__(self, other: float | FloatValue) -> FloatValue: ...
    def __pow__(self, other: int | float | IntValue | FloatValue) -> IntValue | FloatValue:
        from ..morphisms import PowOp
        from ..values import FloatValue, IntValue

        if isinstance(other, (float, FloatValue)):
            return FloatValue(PowOp(self, other))
        return IntValue(PowOp(self, other))

    @overload
    def __rpow__(self, other: int) -> IntValue: ...
    @overload
    def __rpow__(self, other: float) -> FloatValue: ...
    def __rpow__(self, other: int | float) -> IntValue | FloatValue:
        from ..morphisms import PowOp
        from ..values import FloatValue, IntValue

        if isinstance(other, float):
            return FloatValue(PowOp(other, self))
        return IntValue(PowOp(other, self))

    def __neg__(self) -> IntValue:
        from ..morphisms import NegOp
        from ..values import IntValue

        return IntValue(NegOp(self))

    def __pos__(self) -> IntValue:
        from ..morphisms import PosOp
        from ..values import IntValue

        return IntValue(PosOp(self))

    def __abs__(self) -> IntValue:
        from ..morphisms import AbsOp
        from ..values import IntValue

        return IntValue(AbsOp(self))
