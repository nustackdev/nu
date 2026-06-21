"""FloatForm - float interface."""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu2.lang import Form, TypedNu


if TYPE_CHECKING:
    from nu2.lang import BoolArg, FloatArg, IntArg

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
        from nu2.core import Add

        return FloatForm(Add(self, other))

    def __radd__(self, other: IntArg | FloatArg) -> FloatForm:
        from nu2.core import Add

        return FloatForm(Add(other, self))

    def __sub__(self, other: IntArg | FloatArg) -> FloatForm:
        from nu2.core import Sub

        return FloatForm(Sub(self, other))

    def __rsub__(self, other: IntArg | FloatArg) -> FloatForm:
        from nu2.core import Sub

        return FloatForm(Sub(other, self))

    def __mul__(self, other: IntArg | FloatArg) -> FloatForm:
        from nu2.core import Mul

        return FloatForm(Mul(self, other))

    def __rmul__(self, other: IntArg | FloatArg) -> FloatForm:
        from nu2.core import Mul

        return FloatForm(Mul(other, self))

    def __truediv__(self, other: IntArg | FloatArg) -> FloatForm:
        from nu2.core import Div

        return FloatForm(Div(self, other))

    def __rtruediv__(self, other: IntArg | FloatArg) -> FloatForm:
        from nu2.core import Div

        return FloatForm(Div(other, self))

    def __floordiv__(self, other: IntArg | FloatArg) -> FloatForm:
        from nu2.core import FloorDiv

        return FloatForm(FloorDiv(self, other))

    def __rfloordiv__(self, other: IntArg | FloatArg) -> FloatForm:
        from nu2.core import FloorDiv

        return FloatForm(FloorDiv(other, self))

    def __mod__(self, other: IntArg | FloatArg) -> FloatForm:
        from nu2.core import Mod

        return FloatForm(Mod(self, other))

    def __rmod__(self, other: IntArg | FloatArg) -> FloatForm:
        from nu2.core import Mod

        return FloatForm(Mod(other, self))

    def __pow__(self, other: IntArg | FloatArg) -> FloatForm:
        from nu2.core import Pow

        return FloatForm(Pow(self, other))

    def __rpow__(self, other: IntArg | FloatArg) -> FloatForm:
        from nu2.core import Pow

        return FloatForm(Pow(other, self))

    def __neg__(self) -> FloatForm:
        from nu2.core import Neg

        return FloatForm(Neg(self))

    def __pos__(self) -> FloatForm:
        from nu2.core import Pos

        return FloatForm(Pos(self))

    def __abs__(self) -> FloatForm:
        from nu2.core import Abs

        return FloatForm(Abs(self))

    # =========================================================================
    # COMPARISON
    # =========================================================================

    def __gt__(self, other: IntArg | FloatArg) -> BoolForm:
        from nu2.core import Gt

        from .bool_ import BoolForm

        return BoolForm(Gt(self, other))

    def __lt__(self, other: IntArg | FloatArg) -> BoolForm:
        from nu2.core import Lt

        from .bool_ import BoolForm

        return BoolForm(Lt(self, other))

    def __ge__(self, other: IntArg | FloatArg) -> BoolForm:
        from nu2.core import Ge

        from .bool_ import BoolForm

        return BoolForm(Ge(self, other))

    def __le__(self, other: IntArg | FloatArg) -> BoolForm:
        from nu2.core import Le

        from .bool_ import BoolForm

        return BoolForm(Le(self, other))

    __hash__ = object.__hash__

    def __eq__(self, other: IntArg | FloatArg) -> BoolForm:  # type: ignore[override]
        from nu2.core import Eq

        from .bool_ import BoolForm

        return BoolForm(Eq(self, other))

    def __ne__(self, other: IntArg | FloatArg) -> BoolForm:  # type: ignore[override]
        from nu2.core import Ne

        from .bool_ import BoolForm

        return BoolForm(Ne(self, other))

    def is_(self, other: IntArg | FloatArg) -> BoolForm:
        """Identity comparison: self is other."""
        from nu2.core import Is

        from .bool_ import BoolForm

        return BoolForm(Is(self, other))

    # =========================================================================
    # LOGICAL
    # =========================================================================

    def and_(self, other: BoolArg | FloatArg) -> BoolForm:
        """Logical AND: self AND other."""
        from nu2.core import And

        from .bool_ import BoolForm

        return BoolForm(And(self, other))

    def or_(self, other: BoolArg | FloatArg) -> BoolForm:
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
