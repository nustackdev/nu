"""AnyI - dynamic/unknown type interface."""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.interface import Interface


if TYPE_CHECKING:

    from .bool_ import BoolI


__all__ = [
    "AnyI",
]


class AnyI(Interface[object]):
    """Any/dynamic interface. Supports all operations, results stay AnyI."""

    # =========================================================================
    # ARITHMETIC
    # =========================================================================

    def __add__(self, other: object) -> AnyI:
        from nu.ops import AddOp

        return AnyI(AddOp(self, other))

    def __radd__(self, other: object) -> AnyI:
        from nu.ops import AddOp

        return AnyI(AddOp(other, self))

    def __sub__(self, other: object) -> AnyI:
        from nu.ops import SubOp

        return AnyI(SubOp(self, other))

    def __rsub__(self, other: object) -> AnyI:
        from nu.ops import SubOp

        return AnyI(SubOp(other, self))

    def __mul__(self, other: object) -> AnyI:
        from nu.ops import MulOp

        return AnyI(MulOp(self, other))

    def __rmul__(self, other: object) -> AnyI:
        from nu.ops import MulOp

        return AnyI(MulOp(other, self))

    def __truediv__(self, other: object) -> AnyI:
        from nu.ops import DivOp

        return AnyI(DivOp(self, other))

    def __rtruediv__(self, other: object) -> AnyI:
        from nu.ops import DivOp

        return AnyI(DivOp(other, self))

    def __floordiv__(self, other: object) -> AnyI:
        from nu.ops import FloorDivOp

        return AnyI(FloorDivOp(self, other))

    def __rfloordiv__(self, other: object) -> AnyI:
        from nu.ops import FloorDivOp

        return AnyI(FloorDivOp(other, self))

    def __mod__(self, other: object) -> AnyI:
        from nu.ops import ModOp

        return AnyI(ModOp(self, other))

    def __rmod__(self, other: object) -> AnyI:
        from nu.ops import ModOp

        return AnyI(ModOp(other, self))

    def __pow__(self, other: object) -> AnyI:
        from nu.ops import PowOp

        return AnyI(PowOp(self, other))

    def __rpow__(self, other: object) -> AnyI:
        from nu.ops import PowOp

        return AnyI(PowOp(other, self))

    def __neg__(self) -> AnyI:
        from nu.ops import NegOp

        return AnyI(NegOp(self))

    def __pos__(self) -> AnyI:
        from nu.ops import PosOp

        return AnyI(PosOp(self))

    def __abs__(self) -> AnyI:
        from nu.ops import AbsOp

        return AnyI(AbsOp(self))

    # =========================================================================
    # COMPARISON
    # =========================================================================

    def __gt__(self, other: object) -> BoolI:
        from nu.ops import GtOp

        from .bool_ import BoolI

        return BoolI(GtOp(self, other))

    def __lt__(self, other: object) -> BoolI:
        from nu.ops import LtOp

        from .bool_ import BoolI

        return BoolI(LtOp(self, other))

    def __ge__(self, other: object) -> BoolI:
        from nu.ops import GeOp

        from .bool_ import BoolI

        return BoolI(GeOp(self, other))

    def __le__(self, other: object) -> BoolI:
        from nu.ops import LeOp

        from .bool_ import BoolI

        return BoolI(LeOp(self, other))

    def eq(self, other: object) -> BoolI:
        from nu.ops import EqOp

        from .bool_ import BoolI

        return BoolI(EqOp(self, other))

    def ne(self, other: object) -> BoolI:
        from nu.ops import NeOp

        from .bool_ import BoolI

        return BoolI(NeOp(self, other))

    def is_(self, other: object) -> BoolI:
        from nu.ops import IdCompOp

        from .bool_ import BoolI

        return BoolI(IdCompOp(self, other))

    # =========================================================================
    # LOGICAL
    # =========================================================================

    def and_(self, other: object) -> BoolI:
        from nu.ops import AndOp

        from .bool_ import BoolI

        return BoolI(AndOp(self, other))

    def or_(self, other: object) -> BoolI:
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

    def bitand(self, other: object) -> AnyI:
        from nu.ops import BitwiseAndOp

        return AnyI(BitwiseAndOp(self, other))

    def bitor(self, other: object) -> AnyI:
        from nu.ops import BitwiseOrOp

        return AnyI(BitwiseOrOp(self, other))

    def __xor__(self, other: object) -> AnyI:
        from nu.ops import XorOp

        return AnyI(XorOp(self, other))

    def __rxor__(self, other: object) -> AnyI:
        from nu.ops import XorOp

        return AnyI(XorOp(other, self))

    def bitnot(self) -> AnyI:
        from nu.ops import BitwiseNotOp

        return AnyI(BitwiseNotOp(self))

    def __lshift__(self, other: object) -> AnyI:
        from nu.ops import LShiftOp

        return AnyI(LShiftOp(self, other))

    def __rshift__(self, other: object) -> AnyI:
        from nu.ops import RShiftOp

        return AnyI(RShiftOp(self, other))
