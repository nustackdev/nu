"""FloatI - float interface."""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.terms import Interface, TypedNu


if TYPE_CHECKING:
    from nu.terms import BoolArg, FloatArg, IntArg

    from .bool_ import BoolI


__all__ = [
    "FloatI",
]


class FloatI(Interface, TypedNu[float]):
    """Float interface. Numeric + comparable + logical."""

    # =========================================================================
    # ARITHMETIC
    # =========================================================================

    def __add__(self, other: IntArg | FloatArg) -> FloatI:
        from nu import Add

        return FloatI(Add(self, other))

    def __radd__(self, other: IntArg | FloatArg) -> FloatI:
        from nu import Add

        return FloatI(Add(other, self))

    def __sub__(self, other: IntArg | FloatArg) -> FloatI:
        from nu import Sub

        return FloatI(Sub(self, other))

    def __rsub__(self, other: IntArg | FloatArg) -> FloatI:
        from nu import Sub

        return FloatI(Sub(other, self))

    def __mul__(self, other: IntArg | FloatArg) -> FloatI:
        from nu import Mul

        return FloatI(Mul(self, other))

    def __rmul__(self, other: IntArg | FloatArg) -> FloatI:
        from nu import Mul

        return FloatI(Mul(other, self))

    def __truediv__(self, other: IntArg | FloatArg) -> FloatI:
        from nu import Div

        return FloatI(Div(self, other))

    def __rtruediv__(self, other: IntArg | FloatArg) -> FloatI:
        from nu import Div

        return FloatI(Div(other, self))

    def __floordiv__(self, other: IntArg | FloatArg) -> FloatI:
        from nu import FloorDiv

        return FloatI(FloorDiv(self, other))

    def __rfloordiv__(self, other: IntArg | FloatArg) -> FloatI:
        from nu import FloorDiv

        return FloatI(FloorDiv(other, self))

    def __mod__(self, other: IntArg | FloatArg) -> FloatI:
        from nu import Mod

        return FloatI(Mod(self, other))

    def __rmod__(self, other: IntArg | FloatArg) -> FloatI:
        from nu import Mod

        return FloatI(Mod(other, self))

    def __pow__(self, other: IntArg | FloatArg) -> FloatI:
        from nu import Pow

        return FloatI(Pow(self, other))

    def __rpow__(self, other: IntArg | FloatArg) -> FloatI:
        from nu import Pow

        return FloatI(Pow(other, self))

    def __neg__(self) -> FloatI:
        from nu import Neg

        return FloatI(Neg(self))

    def __pos__(self) -> FloatI:
        from nu import Pos

        return FloatI(Pos(self))

    def __abs__(self) -> FloatI:
        from nu import Abs

        return FloatI(Abs(self))

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

    def and_(self, other: BoolArg | FloatArg) -> BoolI:
        from nu import And

        from .bool_ import BoolI

        return BoolI(And(self, other))

    def or_(self, other: BoolArg | FloatArg) -> BoolI:
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
