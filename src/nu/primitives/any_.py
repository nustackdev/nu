"""AnyI - dynamic/unknown type interface."""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.terms import Interface, TypedNu


if TYPE_CHECKING:
    from .bool_ import BoolI


__all__ = [
    "AnyI",
]


class AnyI(Interface, TypedNu[object]):
    """Any/dynamic interface. Supports all operations, results stay AnyI."""

    # =========================================================================
    # ARITHMETIC
    # =========================================================================

    def __add__(self, other: object) -> AnyI:
        from nu import Add

        return AnyI(Add(self, other))

    def __radd__(self, other: object) -> AnyI:
        from nu import Add

        return AnyI(Add(other, self))

    def __sub__(self, other: object) -> AnyI:
        from nu import Sub

        return AnyI(Sub(self, other))

    def __rsub__(self, other: object) -> AnyI:
        from nu import Sub

        return AnyI(Sub(other, self))

    def __mul__(self, other: object) -> AnyI:
        from nu import Mul

        return AnyI(Mul(self, other))

    def __rmul__(self, other: object) -> AnyI:
        from nu import Mul

        return AnyI(Mul(other, self))

    def __truediv__(self, other: object) -> AnyI:
        from nu import Div

        return AnyI(Div(self, other))

    def __rtruediv__(self, other: object) -> AnyI:
        from nu import Div

        return AnyI(Div(other, self))

    def __floordiv__(self, other: object) -> AnyI:
        from nu import FloorDiv

        return AnyI(FloorDiv(self, other))

    def __rfloordiv__(self, other: object) -> AnyI:
        from nu import FloorDiv

        return AnyI(FloorDiv(other, self))

    def __mod__(self, other: object) -> AnyI:
        from nu import Mod

        return AnyI(Mod(self, other))

    def __rmod__(self, other: object) -> AnyI:
        from nu import Mod

        return AnyI(Mod(other, self))

    def __pow__(self, other: object) -> AnyI:
        from nu import Pow

        return AnyI(Pow(self, other))

    def __rpow__(self, other: object) -> AnyI:
        from nu import Pow

        return AnyI(Pow(other, self))

    def __neg__(self) -> AnyI:
        from nu import Neg

        return AnyI(Neg(self))

    def __pos__(self) -> AnyI:
        from nu import Pos

        return AnyI(Pos(self))

    def __abs__(self) -> AnyI:
        from nu import Abs

        return AnyI(Abs(self))

    # =========================================================================
    # COMPARISON
    # =========================================================================

    def __gt__(self, other: object) -> BoolI:
        from nu import Gt

        from .bool_ import BoolI

        return BoolI(Gt(self, other))

    def __lt__(self, other: object) -> BoolI:
        from nu import Lt

        from .bool_ import BoolI

        return BoolI(Lt(self, other))

    def __ge__(self, other: object) -> BoolI:
        from nu import Ge

        from .bool_ import BoolI

        return BoolI(Ge(self, other))

    def __le__(self, other: object) -> BoolI:
        from nu import Le

        from .bool_ import BoolI

        return BoolI(Le(self, other))

    def eq(self, other: object) -> BoolI:
        from nu import Eq

        from .bool_ import BoolI

        return BoolI(Eq(self, other))

    def ne(self, other: object) -> BoolI:
        from nu import Ne

        from .bool_ import BoolI

        return BoolI(Ne(self, other))

    def is_(self, other: object) -> BoolI:
        from nu import IdComp

        from .bool_ import BoolI

        return BoolI(IdComp(self, other))

    # =========================================================================
    # LOGICAL
    # =========================================================================

    def and_(self, other: object) -> BoolI:
        from nu import And

        from .bool_ import BoolI

        return BoolI(And(self, other))

    def or_(self, other: object) -> BoolI:
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

    def bitand(self, other: object) -> AnyI:
        from nu import BitwiseAnd

        return AnyI(BitwiseAnd(self, other))

    def bitor(self, other: object) -> AnyI:
        from nu import BitwiseOr

        return AnyI(BitwiseOr(self, other))

    def __xor__(self, other: object) -> AnyI:
        from nu import Xor

        return AnyI(Xor(self, other))

    def __rxor__(self, other: object) -> AnyI:
        from nu import Xor

        return AnyI(Xor(other, self))

    def bitnot(self) -> AnyI:
        from nu import BitwiseNot

        return AnyI(BitwiseNot(self))

    def __lshift__(self, other: object) -> AnyI:
        from nu import LShift

        return AnyI(LShift(self, other))

    def __rshift__(self, other: object) -> AnyI:
        from nu import RShift

        return AnyI(RShift(self, other))
