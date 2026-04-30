"""IntI - integer interface.

IntI = Interface[int] + arithmetic + comparison + logical + bitwise.
Handles int/float promotion: int op float → FloatI.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, overload

from nu.terms import Interface, TypedNu


if TYPE_CHECKING:
    from nu.terms import BoolArg, FloatArg, IntArg

    from .bool_ import BoolI
    from .float_ import FloatI


__all__ = [
    "IntI",
]


class IntI(Interface, TypedNu[int]):
    """Integer interface. Full numeric + comparable + logical + bitwise."""

    # =========================================================================
    # ARITHMETIC (with int/float promotion)
    # =========================================================================

    @overload
    def __add__(self, other: IntArg) -> IntI: ...
    @overload
    def __add__(self, other: FloatArg) -> FloatI: ...
    def __add__(self, other: IntArg | FloatArg) -> IntI | FloatI:
        from nu import Add

        from .float_ import FloatI

        if isinstance(other, (float, FloatI)):
            return FloatI(Add(self, other))
        return IntI(Add(self, other))

    @overload
    def __radd__(self, other: IntArg) -> IntI: ...
    @overload
    def __radd__(self, other: FloatArg) -> FloatI: ...
    def __radd__(self, other: IntArg | FloatArg) -> IntI | FloatI:
        from nu import Add

        from .float_ import FloatI

        if isinstance(other, float):
            return FloatI(Add(other, self))
        return IntI(Add(other, self))

    @overload
    def __sub__(self, other: IntArg) -> IntI: ...
    @overload
    def __sub__(self, other: FloatArg) -> FloatI: ...
    def __sub__(self, other: IntArg | FloatArg) -> IntI | FloatI:
        from nu import Sub

        from .float_ import FloatI

        if isinstance(other, (float, FloatI)):
            return FloatI(Sub(self, other))
        return IntI(Sub(self, other))

    @overload
    def __rsub__(self, other: IntArg) -> IntI: ...
    @overload
    def __rsub__(self, other: FloatArg) -> FloatI: ...
    def __rsub__(self, other: IntArg | FloatArg) -> IntI | FloatI:
        from nu import Sub

        from .float_ import FloatI

        if isinstance(other, float):
            return FloatI(Sub(other, self))
        return IntI(Sub(other, self))

    @overload
    def __mul__(self, other: IntArg) -> IntI: ...
    @overload
    def __mul__(self, other: FloatArg) -> FloatI: ...
    def __mul__(self, other: IntArg | FloatArg) -> IntI | FloatI:
        from nu import Mul

        from .float_ import FloatI

        if isinstance(other, (float, FloatI)):
            return FloatI(Mul(self, other))
        return IntI(Mul(self, other))

    @overload
    def __rmul__(self, other: IntArg) -> IntI: ...
    @overload
    def __rmul__(self, other: FloatArg) -> FloatI: ...
    def __rmul__(self, other: IntArg | FloatArg) -> IntI | FloatI:
        from nu import Mul

        from .float_ import FloatI

        if isinstance(other, float):
            return FloatI(Mul(other, self))
        return IntI(Mul(other, self))

    def __truediv__(self, other: IntArg | FloatArg) -> FloatI:
        from nu import Div

        from .float_ import FloatI

        return FloatI(Div(self, other))

    def __rtruediv__(self, other: IntArg | FloatArg) -> FloatI:
        from nu import Div

        from .float_ import FloatI

        return FloatI(Div(other, self))

    @overload
    def __floordiv__(self, other: IntArg) -> IntI: ...
    @overload
    def __floordiv__(self, other: FloatArg) -> FloatI: ...
    def __floordiv__(self, other: IntArg | FloatArg) -> IntI | FloatI:
        from nu import FloorDiv

        from .float_ import FloatI

        if isinstance(other, (float, FloatI)):
            return FloatI(FloorDiv(self, other))
        return IntI(FloorDiv(self, other))

    @overload
    def __rfloordiv__(self, other: IntArg) -> IntI: ...
    @overload
    def __rfloordiv__(self, other: FloatArg) -> FloatI: ...
    def __rfloordiv__(self, other: IntArg | FloatArg) -> IntI | FloatI:
        from nu import FloorDiv

        from .float_ import FloatI

        if isinstance(other, float):
            return FloatI(FloorDiv(other, self))
        return IntI(FloorDiv(other, self))

    @overload
    def __mod__(self, other: IntArg) -> IntI: ...
    @overload
    def __mod__(self, other: FloatArg) -> FloatI: ...
    def __mod__(self, other: IntArg | FloatArg) -> IntI | FloatI:
        from nu import Mod

        from .float_ import FloatI

        if isinstance(other, (float, FloatI)):
            return FloatI(Mod(self, other))
        return IntI(Mod(self, other))

    @overload
    def __rmod__(self, other: IntArg) -> IntI: ...
    @overload
    def __rmod__(self, other: FloatArg) -> FloatI: ...
    def __rmod__(self, other: IntArg | FloatArg) -> IntI | FloatI:
        from nu import Mod

        from .float_ import FloatI

        if isinstance(other, float):
            return FloatI(Mod(other, self))
        return IntI(Mod(other, self))

    @overload
    def __pow__(self, other: IntArg) -> IntI: ...
    @overload
    def __pow__(self, other: FloatArg) -> FloatI: ...
    def __pow__(self, other: IntArg | FloatArg) -> IntI | FloatI:
        from nu import Pow

        from .float_ import FloatI

        if isinstance(other, (float, FloatI)):
            return FloatI(Pow(self, other))
        return IntI(Pow(self, other))

    @overload
    def __rpow__(self, other: IntArg) -> IntI: ...
    @overload
    def __rpow__(self, other: FloatArg) -> FloatI: ...
    def __rpow__(self, other: IntArg | FloatArg) -> IntI | FloatI:
        from nu import Pow

        from .float_ import FloatI

        if isinstance(other, float):
            return FloatI(Pow(other, self))
        return IntI(Pow(other, self))

    def __neg__(self) -> IntI:
        from nu import Neg

        return IntI(Neg(self))

    def __pos__(self) -> IntI:
        from nu import Pos

        return IntI(Pos(self))

    def __abs__(self) -> IntI:
        from nu import Abs

        return IntI(Abs(self))

    # =========================================================================
    # COMPARISON
    # =========================================================================

    def __gt__(self, other: IntArg | FloatArg) -> BoolI:
        from nu import Gt

        from .bool_ import BoolI

        return BoolI(Gt(self, other))

    def __lt__(self, other: IntArg | FloatArg) -> BoolI:
        from nu import Lt

        from .bool_ import BoolI

        return BoolI(Lt(self, other))

    def __ge__(self, other: IntArg | FloatArg) -> BoolI:
        from nu import Ge

        from .bool_ import BoolI

        return BoolI(Ge(self, other))

    def __le__(self, other: IntArg | FloatArg) -> BoolI:
        from nu import Le

        from .bool_ import BoolI

        return BoolI(Le(self, other))

    def eq(self, other: IntArg | FloatArg) -> BoolI:
        from nu import Eq

        from .bool_ import BoolI

        return BoolI(Eq(self, other))

    def ne(self, other: IntArg | FloatArg) -> BoolI:
        from nu import Ne

        from .bool_ import BoolI

        return BoolI(Ne(self, other))

    def is_(self, other: IntArg | FloatArg) -> BoolI:
        from nu import IdComp

        from .bool_ import BoolI

        return BoolI(IdComp(self, other))

    # =========================================================================
    # LOGICAL
    # =========================================================================

    def and_(self, other: BoolArg | IntArg) -> BoolI:
        from nu import And

        from .bool_ import BoolI

        return BoolI(And(self, other))

    def or_(self, other: BoolArg | IntArg) -> BoolI:
        from nu import Or

        from .bool_ import BoolI

        return BoolI(Or(self, other))

    def not_(self) -> BoolI:
        from nu import Not

        from .bool_ import BoolI

        return BoolI(Not(self))

    def bool_(self) -> BoolI:
        from nu import Bool

        from .bool_ import BoolI

        return BoolI(Bool(self))

    # =========================================================================
    # BITWISE
    # =========================================================================

    def bitand(self, other: IntArg) -> IntI:
        from nu import BitwiseAnd

        return IntI(BitwiseAnd(self, other))

    def bitor(self, other: IntArg) -> IntI:
        from nu import BitwiseOr

        return IntI(BitwiseOr(self, other))

    def __xor__(self, other: IntArg) -> IntI:
        from nu import Xor

        return IntI(Xor(self, other))

    def __rxor__(self, other: IntArg) -> IntI:
        from nu import Xor

        return IntI(Xor(other, self))

    def bitnot(self) -> IntI:
        from nu import BitwiseNot

        return IntI(BitwiseNot(self))

    def __lshift__(self, other: IntArg) -> IntI:
        from nu import LShift

        return IntI(LShift(self, other))

    def __rlshift__(self, other: IntArg) -> IntI:
        from nu import LShift

        return IntI(LShift(other, self))

    def __rshift__(self, other: IntArg) -> IntI:
        from nu import RShift

        return IntI(RShift(self, other))

    def __rrshift__(self, other: IntArg) -> IntI:
        from nu import RShift

        return IntI(RShift(other, self))
