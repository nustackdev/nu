"""IntI - integer interface.

IntI = Interface[int] + arithmetic + comparison + logical + bitwise.
Handles int/float promotion: int op float → FloatI.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, overload

from ..interface import Interface


if TYPE_CHECKING:
    from nu.terms import BoolArg, FloatArg, IntArg

    from .bool_ import BoolI
    from .float_ import FloatI


__all__ = [
    "IntI",
]


class IntI(Interface[int]):
    """Integer interface. Full numeric + comparable + logical + bitwise."""

    # =========================================================================
    # ARITHMETIC (with int/float promotion)
    # =========================================================================

    @overload
    def __add__(self, other: IntArg) -> IntI: ...
    @overload
    def __add__(self, other: FloatArg) -> FloatI: ...
    def __add__(self, other: IntArg | FloatArg) -> IntI | FloatI:
        from nu.ops import AddOp

        from .float_ import FloatI

        if isinstance(other, (float, FloatI)):
            return FloatI(AddOp(self, other))
        return IntI(AddOp(self, other))

    @overload
    def __radd__(self, other: IntArg) -> IntI: ...
    @overload
    def __radd__(self, other: FloatArg) -> FloatI: ...
    def __radd__(self, other: IntArg | FloatArg) -> IntI | FloatI:
        from nu.ops import AddOp

        from .float_ import FloatI

        if isinstance(other, float):
            return FloatI(AddOp(other, self))
        return IntI(AddOp(other, self))

    @overload
    def __sub__(self, other: IntArg) -> IntI: ...
    @overload
    def __sub__(self, other: FloatArg) -> FloatI: ...
    def __sub__(self, other: IntArg | FloatArg) -> IntI | FloatI:
        from nu.ops import SubOp

        from .float_ import FloatI

        if isinstance(other, (float, FloatI)):
            return FloatI(SubOp(self, other))
        return IntI(SubOp(self, other))

    @overload
    def __rsub__(self, other: IntArg) -> IntI: ...
    @overload
    def __rsub__(self, other: FloatArg) -> FloatI: ...
    def __rsub__(self, other: IntArg | FloatArg) -> IntI | FloatI:
        from nu.ops import SubOp

        from .float_ import FloatI

        if isinstance(other, float):
            return FloatI(SubOp(other, self))
        return IntI(SubOp(other, self))

    @overload
    def __mul__(self, other: IntArg) -> IntI: ...
    @overload
    def __mul__(self, other: FloatArg) -> FloatI: ...
    def __mul__(self, other: IntArg | FloatArg) -> IntI | FloatI:
        from nu.ops import MulOp

        from .float_ import FloatI

        if isinstance(other, (float, FloatI)):
            return FloatI(MulOp(self, other))
        return IntI(MulOp(self, other))

    @overload
    def __rmul__(self, other: IntArg) -> IntI: ...
    @overload
    def __rmul__(self, other: FloatArg) -> FloatI: ...
    def __rmul__(self, other: IntArg | FloatArg) -> IntI | FloatI:
        from nu.ops import MulOp

        from .float_ import FloatI

        if isinstance(other, float):
            return FloatI(MulOp(other, self))
        return IntI(MulOp(other, self))

    def __truediv__(self, other: IntArg | FloatArg) -> FloatI:
        from nu.ops import DivOp

        from .float_ import FloatI

        return FloatI(DivOp(self, other))

    def __rtruediv__(self, other: IntArg | FloatArg) -> FloatI:
        from nu.ops import DivOp

        from .float_ import FloatI

        return FloatI(DivOp(other, self))

    @overload
    def __floordiv__(self, other: IntArg) -> IntI: ...
    @overload
    def __floordiv__(self, other: FloatArg) -> FloatI: ...
    def __floordiv__(self, other: IntArg | FloatArg) -> IntI | FloatI:
        from nu.ops import FloorDivOp

        from .float_ import FloatI

        if isinstance(other, (float, FloatI)):
            return FloatI(FloorDivOp(self, other))
        return IntI(FloorDivOp(self, other))

    @overload
    def __rfloordiv__(self, other: IntArg) -> IntI: ...
    @overload
    def __rfloordiv__(self, other: FloatArg) -> FloatI: ...
    def __rfloordiv__(self, other: IntArg | FloatArg) -> IntI | FloatI:
        from nu.ops import FloorDivOp

        from .float_ import FloatI

        if isinstance(other, float):
            return FloatI(FloorDivOp(other, self))
        return IntI(FloorDivOp(other, self))

    @overload
    def __mod__(self, other: IntArg) -> IntI: ...
    @overload
    def __mod__(self, other: FloatArg) -> FloatI: ...
    def __mod__(self, other: IntArg | FloatArg) -> IntI | FloatI:
        from nu.ops import ModOp

        from .float_ import FloatI

        if isinstance(other, (float, FloatI)):
            return FloatI(ModOp(self, other))
        return IntI(ModOp(self, other))

    @overload
    def __rmod__(self, other: IntArg) -> IntI: ...
    @overload
    def __rmod__(self, other: FloatArg) -> FloatI: ...
    def __rmod__(self, other: IntArg | FloatArg) -> IntI | FloatI:
        from nu.ops import ModOp

        from .float_ import FloatI

        if isinstance(other, float):
            return FloatI(ModOp(other, self))
        return IntI(ModOp(other, self))

    @overload
    def __pow__(self, other: IntArg) -> IntI: ...
    @overload
    def __pow__(self, other: FloatArg) -> FloatI: ...
    def __pow__(self, other: IntArg | FloatArg) -> IntI | FloatI:
        from nu.ops import PowOp

        from .float_ import FloatI

        if isinstance(other, (float, FloatI)):
            return FloatI(PowOp(self, other))
        return IntI(PowOp(self, other))

    @overload
    def __rpow__(self, other: IntArg) -> IntI: ...
    @overload
    def __rpow__(self, other: FloatArg) -> FloatI: ...
    def __rpow__(self, other: IntArg | FloatArg) -> IntI | FloatI:
        from nu.ops import PowOp

        from .float_ import FloatI

        if isinstance(other, float):
            return FloatI(PowOp(other, self))
        return IntI(PowOp(other, self))

    def __neg__(self) -> IntI:
        from nu.ops import NegOp

        return IntI(NegOp(self))

    def __pos__(self) -> IntI:
        from nu.ops import PosOp

        return IntI(PosOp(self))

    def __abs__(self) -> IntI:
        from nu.ops import AbsOp

        return IntI(AbsOp(self))

    # =========================================================================
    # COMPARISON
    # =========================================================================

    def __gt__(self, other: IntArg | FloatArg) -> BoolI:
        from nu.ops import GtOp

        from .bool_ import BoolI

        return BoolI(GtOp(self, other))

    def __lt__(self, other: IntArg | FloatArg) -> BoolI:
        from nu.ops import LtOp

        from .bool_ import BoolI

        return BoolI(LtOp(self, other))

    def __ge__(self, other: IntArg | FloatArg) -> BoolI:
        from nu.ops import GeOp

        from .bool_ import BoolI

        return BoolI(GeOp(self, other))

    def __le__(self, other: IntArg | FloatArg) -> BoolI:
        from nu.ops import LeOp

        from .bool_ import BoolI

        return BoolI(LeOp(self, other))

    def eq(self, other: IntArg | FloatArg) -> BoolI:
        from nu.ops import EqOp

        from .bool_ import BoolI

        return BoolI(EqOp(self, other))

    def ne(self, other: IntArg | FloatArg) -> BoolI:
        from nu.ops import NeOp

        from .bool_ import BoolI

        return BoolI(NeOp(self, other))

    def is_(self, other: IntArg | FloatArg) -> BoolI:
        from nu.ops import IdCompOp

        from .bool_ import BoolI

        return BoolI(IdCompOp(self, other))

    # =========================================================================
    # LOGICAL
    # =========================================================================

    def and_(self, other: BoolArg | IntArg) -> BoolI:
        from nu.ops import AndOp

        from .bool_ import BoolI

        return BoolI(AndOp(self, other))

    def or_(self, other: BoolArg | IntArg) -> BoolI:
        from nu.ops import OrOp

        from .bool_ import BoolI

        return BoolI(OrOp(self, other))

    def not_(self) -> BoolI:
        from nu.ops import NotOp

        from .bool_ import BoolI

        return BoolI(NotOp(self))

    def bool_(self) -> BoolI:
        from nu.ops import BoolOp

        from .bool_ import BoolI

        return BoolI(BoolOp(self))

    # =========================================================================
    # BITWISE
    # =========================================================================

    def bitand(self, other: IntArg) -> IntI:
        from nu.ops import BitwiseAndOp

        return IntI(BitwiseAndOp(self, other))

    def bitor(self, other: IntArg) -> IntI:
        from nu.ops import BitwiseOrOp

        return IntI(BitwiseOrOp(self, other))

    def __xor__(self, other: IntArg) -> IntI:
        from nu.ops import XorOp

        return IntI(XorOp(self, other))

    def __rxor__(self, other: IntArg) -> IntI:
        from nu.ops import XorOp

        return IntI(XorOp(other, self))

    def bitnot(self) -> IntI:
        from nu.ops import BitwiseNotOp

        return IntI(BitwiseNotOp(self))

    def __lshift__(self, other: IntArg) -> IntI:
        from nu.ops import LShiftOp

        return IntI(LShiftOp(self, other))

    def __rlshift__(self, other: IntArg) -> IntI:
        from nu.ops import LShiftOp

        return IntI(LShiftOp(other, self))

    def __rshift__(self, other: IntArg) -> IntI:
        from nu.ops import RShiftOp

        return IntI(RShiftOp(self, other))

    def __rrshift__(self, other: IntArg) -> IntI:
        from nu.ops import RShiftOp

        return IntI(RShiftOp(other, self))
