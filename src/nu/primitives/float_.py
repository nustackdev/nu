"""FloatI - float interface."""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.interface import Interface, TypedNu


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
        from nu.ops import AddOp

        return FloatI(AddOp(self, other))

    def __radd__(self, other: IntArg | FloatArg) -> FloatI:
        from nu.ops import AddOp

        return FloatI(AddOp(other, self))

    def __sub__(self, other: IntArg | FloatArg) -> FloatI:
        from nu.ops import SubOp

        return FloatI(SubOp(self, other))

    def __rsub__(self, other: IntArg | FloatArg) -> FloatI:
        from nu.ops import SubOp

        return FloatI(SubOp(other, self))

    def __mul__(self, other: IntArg | FloatArg) -> FloatI:
        from nu.ops import MulOp

        return FloatI(MulOp(self, other))

    def __rmul__(self, other: IntArg | FloatArg) -> FloatI:
        from nu.ops import MulOp

        return FloatI(MulOp(other, self))

    def __truediv__(self, other: IntArg | FloatArg) -> FloatI:
        from nu.ops import DivOp

        return FloatI(DivOp(self, other))

    def __rtruediv__(self, other: IntArg | FloatArg) -> FloatI:
        from nu.ops import DivOp

        return FloatI(DivOp(other, self))

    def __floordiv__(self, other: IntArg | FloatArg) -> FloatI:
        from nu.ops import FloorDivOp

        return FloatI(FloorDivOp(self, other))

    def __rfloordiv__(self, other: IntArg | FloatArg) -> FloatI:
        from nu.ops import FloorDivOp

        return FloatI(FloorDivOp(other, self))

    def __mod__(self, other: IntArg | FloatArg) -> FloatI:
        from nu.ops import ModOp

        return FloatI(ModOp(self, other))

    def __rmod__(self, other: IntArg | FloatArg) -> FloatI:
        from nu.ops import ModOp

        return FloatI(ModOp(other, self))

    def __pow__(self, other: IntArg | FloatArg) -> FloatI:
        from nu.ops import PowOp

        return FloatI(PowOp(self, other))

    def __rpow__(self, other: IntArg | FloatArg) -> FloatI:
        from nu.ops import PowOp

        return FloatI(PowOp(other, self))

    def __neg__(self) -> FloatI:
        from nu.ops import NegOp

        return FloatI(NegOp(self))

    def __pos__(self) -> FloatI:
        from nu.ops import PosOp

        return FloatI(PosOp(self))

    def __abs__(self) -> FloatI:
        from nu.ops import AbsOp

        return FloatI(AbsOp(self))

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

    def and_(self, other: BoolArg | FloatArg) -> BoolI:
        from nu.ops import AndOp

        from .bool_ import BoolI

        return BoolI(AndOp(self, other))

    def or_(self, other: BoolArg | FloatArg) -> BoolI:
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
