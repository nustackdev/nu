"""AnyForm - dynamic/unknown type interface."""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu2.lang import Form, TypedNu


if TYPE_CHECKING:
    from .bool_ import BoolForm


__all__ = [
    "AnyForm",
]


class AnyForm(Form, TypedNu[object]):
    """Any/dynamic interface. Supports all operations, results stay AnyForm."""

    # =========================================================================
    # ARITHMETIC
    # =========================================================================

    def __add__(self, other: object) -> AnyForm:
        from nu2.core import Add

        return AnyForm(Add(self, other))

    def __radd__(self, other: object) -> AnyForm:
        from nu2.core import Add

        return AnyForm(Add(other, self))

    def __sub__(self, other: object) -> AnyForm:
        from nu2.core import Sub

        return AnyForm(Sub(self, other))

    def __rsub__(self, other: object) -> AnyForm:
        from nu2.core import Sub

        return AnyForm(Sub(other, self))

    def __mul__(self, other: object) -> AnyForm:
        from nu2.core import Mul

        return AnyForm(Mul(self, other))

    def __rmul__(self, other: object) -> AnyForm:
        from nu2.core import Mul

        return AnyForm(Mul(other, self))

    def __truediv__(self, other: object) -> AnyForm:
        from nu2.core import Div

        return AnyForm(Div(self, other))

    def __rtruediv__(self, other: object) -> AnyForm:
        from nu2.core import Div

        return AnyForm(Div(other, self))

    def __floordiv__(self, other: object) -> AnyForm:
        from nu2.core import FloorDiv

        return AnyForm(FloorDiv(self, other))

    def __rfloordiv__(self, other: object) -> AnyForm:
        from nu2.core import FloorDiv

        return AnyForm(FloorDiv(other, self))

    def __mod__(self, other: object) -> AnyForm:
        from nu2.core import Mod

        return AnyForm(Mod(self, other))

    def __rmod__(self, other: object) -> AnyForm:
        from nu2.core import Mod

        return AnyForm(Mod(other, self))

    def __pow__(self, other: object) -> AnyForm:
        from nu2.core import Pow

        return AnyForm(Pow(self, other))

    def __rpow__(self, other: object) -> AnyForm:
        from nu2.core import Pow

        return AnyForm(Pow(other, self))

    def __neg__(self) -> AnyForm:
        from nu2.core import Neg

        return AnyForm(Neg(self))

    def __pos__(self) -> AnyForm:
        from nu2.core import Pos

        return AnyForm(Pos(self))

    def __abs__(self) -> AnyForm:
        from nu2.core import Abs

        return AnyForm(Abs(self))

    # =========================================================================
    # COMPARISON
    # =========================================================================

    def __gt__(self, other: object) -> BoolForm:
        from nu2.core import Gt

        from .bool_ import BoolForm

        return BoolForm(Gt(self, other))

    def __lt__(self, other: object) -> BoolForm:
        from nu2.core import Lt

        from .bool_ import BoolForm

        return BoolForm(Lt(self, other))

    def __ge__(self, other: object) -> BoolForm:
        from nu2.core import Ge

        from .bool_ import BoolForm

        return BoolForm(Ge(self, other))

    def __le__(self, other: object) -> BoolForm:
        from nu2.core import Le

        from .bool_ import BoolForm

        return BoolForm(Le(self, other))

    __hash__ = object.__hash__

    def __eq__(self, other: object) -> BoolForm:  # type: ignore[override]
        from nu2.core import Eq

        from .bool_ import BoolForm

        return BoolForm(Eq(self, other))

    def __ne__(self, other: object) -> BoolForm:  # type: ignore[override]
        from nu2.core import Ne

        from .bool_ import BoolForm

        return BoolForm(Ne(self, other))

    def is_(self, other: object) -> BoolForm:
        """Identity comparison: self is other."""
        from nu2.core import Is

        from .bool_ import BoolForm

        return BoolForm(Is(self, other))

    # =========================================================================
    # LOGICAL
    # =========================================================================

    def and_(self, other: object) -> BoolForm:
        """Logical AND: self AND other."""
        from nu2.core import And

        from .bool_ import BoolForm

        return BoolForm(And(self, other))

    def or_(self, other: object) -> BoolForm:
        """Logical OR: self OR other."""
        from nu2.core import Or

        from .bool_ import BoolForm

        return BoolForm(Or(self, other))

    def not_(self) -> BoolForm:
        """Logical NOT: NOT self."""
        from nu2.core import Not

        from .bool_ import BoolForm

        return BoolForm(Not(self))

    def bool_(self) -> BoolForm:
        """Convert to boolean."""
        from nu2.core import Bool

        from .bool_ import BoolForm

        return BoolForm(Bool(self))

    # =========================================================================
    # BITWISE
    # =========================================================================

    def bitand(self, other: object) -> AnyForm:
        """Bitwise AND: self & other."""
        from nu2.core import BitAnd

        return AnyForm(BitAnd(self, other))

    def bitor(self, other: object) -> AnyForm:
        """Bitwise OR: self | other."""
        from nu2.core import BitOr

        return AnyForm(BitOr(self, other))

    def __xor__(self, other: object) -> AnyForm:
        from nu2.core import BitXor

        return AnyForm(BitXor(self, other))

    def __rxor__(self, other: object) -> AnyForm:
        from nu2.core import BitXor

        return AnyForm(BitXor(other, self))

    def bitnot(self) -> AnyForm:
        """Bitwise NOT: ~self."""
        from nu2.core import BitNot

        return AnyForm(BitNot(self))

    def __lshift__(self, other: object) -> AnyForm:
        from nu2.core import LShift

        return AnyForm(LShift(self, other))

    def __rshift__(self, other: object) -> AnyForm:
        from nu2.core import RShift

        return AnyForm(RShift(self, other))
