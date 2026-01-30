"""Integer ref base combining numeric traits.

IntRef = RefBase[int] + Numeric + Comparable + Logical + Bitwise

Returns concrete py types (IntRef, FloatRef, BoolRef).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, overload

from everybase.capabilities import BitwiseBase, ComparableBase, LogicalBase

from ._base import RefBase


if TYPE_CHECKING:
    from everyabc import Term
    from everybase.py import BoolRef, FloatRef, IntRef


__all__ = [
    "IntRefBase",
]


class IntRefBase(
    ComparableBase["int | float | IntRef | FloatRef"],
    LogicalBase["bool | int | BoolRef | IntRef", "BoolRef"],
    BitwiseBase["int | IntRef", "IntRef"],
    RefBase[int],
):
    """Abstract base for integer refs.

    Combines traits and returns concrete py types.
    """

    def _wrap_bitwise_result(self, operand: Term) -> IntRef:
        from everybase.py import IntRef

        return IntRef(operand)

    def _wrap_logical_result(self, operand: Term) -> BoolRef:
        from everybase.py import BoolRef

        return BoolRef(operand)

    # =========================================================================
    # ARITHMETIC (with int/float promotion)
    # =========================================================================

    @overload
    def __add__(self, other: int | IntRef) -> IntRef: ...
    @overload
    def __add__(self, other: float | FloatRef) -> FloatRef: ...
    def __add__(self, other: int | float | IntRef | FloatRef) -> IntRef | FloatRef:
        from everybase.morphisms import AddOp
        from everybase.py import FloatRef, IntRef

        if isinstance(other, (float, FloatRef)):
            return FloatRef(AddOp(self, other))
        return IntRef(AddOp(self, other))

    @overload
    def __radd__(self, other: int) -> IntRef: ...
    @overload
    def __radd__(self, other: float) -> FloatRef: ...
    def __radd__(self, other: int | float) -> IntRef | FloatRef:
        from everybase.morphisms import AddOp
        from everybase.py import FloatRef, IntRef

        if isinstance(other, float):
            return FloatRef(AddOp(other, self))
        return IntRef(AddOp(other, self))

    @overload
    def __sub__(self, other: int | IntRef) -> IntRef: ...
    @overload
    def __sub__(self, other: float | FloatRef) -> FloatRef: ...
    def __sub__(self, other: int | float | IntRef | FloatRef) -> IntRef | FloatRef:
        from everybase.morphisms import SubOp
        from everybase.py import FloatRef, IntRef

        if isinstance(other, (float, FloatRef)):
            return FloatRef(SubOp(self, other))
        return IntRef(SubOp(self, other))

    @overload
    def __rsub__(self, other: int) -> IntRef: ...
    @overload
    def __rsub__(self, other: float) -> FloatRef: ...
    def __rsub__(self, other: int | float) -> IntRef | FloatRef:
        from everybase.morphisms import SubOp
        from everybase.py import FloatRef, IntRef

        if isinstance(other, float):
            return FloatRef(SubOp(other, self))
        return IntRef(SubOp(other, self))

    @overload
    def __mul__(self, other: int | IntRef) -> IntRef: ...
    @overload
    def __mul__(self, other: float | FloatRef) -> FloatRef: ...
    def __mul__(self, other: int | float | IntRef | FloatRef) -> IntRef | FloatRef:
        from everybase.morphisms import MulOp
        from everybase.py import FloatRef, IntRef

        if isinstance(other, (float, FloatRef)):
            return FloatRef(MulOp(self, other))
        return IntRef(MulOp(self, other))

    @overload
    def __rmul__(self, other: int) -> IntRef: ...
    @overload
    def __rmul__(self, other: float) -> FloatRef: ...
    def __rmul__(self, other: int | float) -> IntRef | FloatRef:
        from everybase.morphisms import MulOp
        from everybase.py import FloatRef, IntRef

        if isinstance(other, float):
            return FloatRef(MulOp(other, self))
        return IntRef(MulOp(other, self))

    def __truediv__(self, other: int | float | IntRef | FloatRef) -> FloatRef:
        from everybase.morphisms import DivOp
        from everybase.py import FloatRef

        return FloatRef(DivOp(self, other))

    def __rtruediv__(self, other: int | float) -> FloatRef:
        from everybase.morphisms import DivOp
        from everybase.py import FloatRef

        return FloatRef(DivOp(other, self))

    @overload
    def __floordiv__(self, other: int | IntRef) -> IntRef: ...
    @overload
    def __floordiv__(self, other: float | FloatRef) -> FloatRef: ...
    def __floordiv__(self, other: int | float | IntRef | FloatRef) -> IntRef | FloatRef:
        from everybase.morphisms import FloorDivOp
        from everybase.py import FloatRef, IntRef

        if isinstance(other, (float, FloatRef)):
            return FloatRef(FloorDivOp(self, other))
        return IntRef(FloorDivOp(self, other))

    @overload
    def __rfloordiv__(self, other: int) -> IntRef: ...
    @overload
    def __rfloordiv__(self, other: float) -> FloatRef: ...
    def __rfloordiv__(self, other: int | float) -> IntRef | FloatRef:
        from everybase.morphisms import FloorDivOp
        from everybase.py import FloatRef, IntRef

        if isinstance(other, float):
            return FloatRef(FloorDivOp(other, self))
        return IntRef(FloorDivOp(other, self))

    @overload
    def __mod__(self, other: int | IntRef) -> IntRef: ...
    @overload
    def __mod__(self, other: float | FloatRef) -> FloatRef: ...
    def __mod__(self, other: int | float | IntRef | FloatRef) -> IntRef | FloatRef:
        from everybase.morphisms import ModOp
        from everybase.py import FloatRef, IntRef

        if isinstance(other, (float, FloatRef)):
            return FloatRef(ModOp(self, other))
        return IntRef(ModOp(self, other))

    @overload
    def __rmod__(self, other: int) -> IntRef: ...
    @overload
    def __rmod__(self, other: float) -> FloatRef: ...
    def __rmod__(self, other: int | float) -> IntRef | FloatRef:
        from everybase.morphisms import ModOp
        from everybase.py import FloatRef, IntRef

        if isinstance(other, float):
            return FloatRef(ModOp(other, self))
        return IntRef(ModOp(other, self))

    @overload
    def __pow__(self, other: int | IntRef) -> IntRef: ...
    @overload
    def __pow__(self, other: float | FloatRef) -> FloatRef: ...
    def __pow__(self, other: int | float | IntRef | FloatRef) -> IntRef | FloatRef:
        from everybase.morphisms import PowOp
        from everybase.py import FloatRef, IntRef

        if isinstance(other, (float, FloatRef)):
            return FloatRef(PowOp(self, other))
        return IntRef(PowOp(self, other))

    @overload
    def __rpow__(self, other: int) -> IntRef: ...
    @overload
    def __rpow__(self, other: float) -> FloatRef: ...
    def __rpow__(self, other: int | float) -> IntRef | FloatRef:
        from everybase.morphisms import PowOp
        from everybase.py import FloatRef, IntRef

        if isinstance(other, float):
            return FloatRef(PowOp(other, self))
        return IntRef(PowOp(other, self))

    def __neg__(self) -> IntRef:
        from everybase.morphisms import NegOp
        from everybase.py import IntRef

        return IntRef(NegOp(self))

    def __pos__(self) -> IntRef:
        from everybase.morphisms import PosOp
        from everybase.py import IntRef

        return IntRef(PosOp(self))

    def __abs__(self) -> IntRef:
        from everybase.morphisms import AbsOp
        from everybase.py import IntRef

        return IntRef(AbsOp(self))
