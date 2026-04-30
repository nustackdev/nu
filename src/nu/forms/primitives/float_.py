"""FloatForm - float interface."""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.terms import Form, TypedNu


if TYPE_CHECKING:
    from nu.terms import BoolArg, FloatArg, IntArg

    from .bool_ import BoolForm


__all__ = [
    "FloatForm",
]


class FloatForm(Form, TypedNu[float]):
    """Float interface. Numeric + comparable + logical."""

    # =========================================================================
    # ARITHMETIC
    # =========================================================================

    def __add__(self, other: IntArg | FloatArg) -> FloatForm:
        from nu import Add

        return FloatForm(Add(self, other))

    def __radd__(self, other: IntArg | FloatArg) -> FloatForm:
        from nu import Add

        return FloatForm(Add(other, self))

    def __sub__(self, other: IntArg | FloatArg) -> FloatForm:
        from nu import Sub

        return FloatForm(Sub(self, other))

    def __rsub__(self, other: IntArg | FloatArg) -> FloatForm:
        from nu import Sub

        return FloatForm(Sub(other, self))

    def __mul__(self, other: IntArg | FloatArg) -> FloatForm:
        from nu import Mul

        return FloatForm(Mul(self, other))

    def __rmul__(self, other: IntArg | FloatArg) -> FloatForm:
        from nu import Mul

        return FloatForm(Mul(other, self))

    def __truediv__(self, other: IntArg | FloatArg) -> FloatForm:
        from nu import Div

        return FloatForm(Div(self, other))

    def __rtruediv__(self, other: IntArg | FloatArg) -> FloatForm:
        from nu import Div

        return FloatForm(Div(other, self))

    def __floordiv__(self, other: IntArg | FloatArg) -> FloatForm:
        from nu import FloorDiv

        return FloatForm(FloorDiv(self, other))

    def __rfloordiv__(self, other: IntArg | FloatArg) -> FloatForm:
        from nu import FloorDiv

        return FloatForm(FloorDiv(other, self))

    def __mod__(self, other: IntArg | FloatArg) -> FloatForm:
        from nu import Mod

        return FloatForm(Mod(self, other))

    def __rmod__(self, other: IntArg | FloatArg) -> FloatForm:
        from nu import Mod

        return FloatForm(Mod(other, self))

    def __pow__(self, other: IntArg | FloatArg) -> FloatForm:
        from nu import Pow

        return FloatForm(Pow(self, other))

    def __rpow__(self, other: IntArg | FloatArg) -> FloatForm:
        from nu import Pow

        return FloatForm(Pow(other, self))

    def __neg__(self) -> FloatForm:
        from nu import Neg

        return FloatForm(Neg(self))

    def __pos__(self) -> FloatForm:
        from nu import Pos

        return FloatForm(Pos(self))

    def __abs__(self) -> FloatForm:
        from nu import Abs

        return FloatForm(Abs(self))

    # =========================================================================
    # COMPARISON
    # =========================================================================

    def __gt__(self, other: IntArg | FloatArg) -> BoolForm:
        from nu import Gt

        from .bool_ import BoolForm

        return BoolForm(Gt(self, other))

    def __lt__(self, other: IntArg | FloatArg) -> BoolForm:
        from nu import Lt

        from .bool_ import BoolForm

        return BoolForm(Lt(self, other))

    def __ge__(self, other: IntArg | FloatArg) -> BoolForm:
        from nu import Ge

        from .bool_ import BoolForm

        return BoolForm(Ge(self, other))

    def __le__(self, other: IntArg | FloatArg) -> BoolForm:
        from nu import Le

        from .bool_ import BoolForm

        return BoolForm(Le(self, other))

    def eq(self, other: IntArg | FloatArg) -> BoolForm:
        from nu import Eq

        from .bool_ import BoolForm

        return BoolForm(Eq(self, other))

    def ne(self, other: IntArg | FloatArg) -> BoolForm:
        from nu import Ne

        from .bool_ import BoolForm

        return BoolForm(Ne(self, other))

    def is_(self, other: IntArg | FloatArg) -> BoolForm:
        from nu import IdComp

        from .bool_ import BoolForm

        return BoolForm(IdComp(self, other))

    # =========================================================================
    # LOGICAL
    # =========================================================================

    def and_(self, other: BoolArg | FloatArg) -> BoolForm:
        from nu import And

        from .bool_ import BoolForm

        return BoolForm(And(self, other))

    def or_(self, other: BoolArg | FloatArg) -> BoolForm:
        from nu import Or

        from .bool_ import BoolForm

        return BoolForm(Or(self, other))

    def not_(self) -> BoolForm:
        from nu import Not

        from .bool_ import BoolForm

        return BoolForm(Not(self))

    def bool_(self) -> BoolForm:
        from nu import Bool

        from .bool_ import BoolForm

        return BoolForm(Bool(self))
