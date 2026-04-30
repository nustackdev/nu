"""IntForm - integer interface.

IntForm = Form[int] + arithmetic + comparison + logical + bitwise.
Handles int/float promotion: int op float → FloatForm.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, overload

from nu.terms import Form, TypedNu


if TYPE_CHECKING:
    from nu.terms import BoolArg, FloatArg, IntArg

    from .bool_ import BoolForm
    from .float_ import FloatForm


__all__ = [
    "IntForm",
]


class IntForm(Form, TypedNu[int]):
    """Integer interface. Full numeric + comparable + logical + bitwise."""

    # =========================================================================
    # ARITHMETIC (with int/float promotion)
    # =========================================================================

    @overload
    def __add__(self, other: IntArg) -> IntForm: ...
    @overload
    def __add__(self, other: FloatArg) -> FloatForm: ...
    def __add__(self, other: IntArg | FloatArg) -> IntForm | FloatForm:
        from nu import Add

        from .float_ import FloatForm

        if isinstance(other, (float, FloatForm)):
            return FloatForm(Add(self, other))
        return IntForm(Add(self, other))

    @overload
    def __radd__(self, other: IntArg) -> IntForm: ...
    @overload
    def __radd__(self, other: FloatArg) -> FloatForm: ...
    def __radd__(self, other: IntArg | FloatArg) -> IntForm | FloatForm:
        from nu import Add

        from .float_ import FloatForm

        if isinstance(other, float):
            return FloatForm(Add(other, self))
        return IntForm(Add(other, self))

    @overload
    def __sub__(self, other: IntArg) -> IntForm: ...
    @overload
    def __sub__(self, other: FloatArg) -> FloatForm: ...
    def __sub__(self, other: IntArg | FloatArg) -> IntForm | FloatForm:
        from nu import Sub

        from .float_ import FloatForm

        if isinstance(other, (float, FloatForm)):
            return FloatForm(Sub(self, other))
        return IntForm(Sub(self, other))

    @overload
    def __rsub__(self, other: IntArg) -> IntForm: ...
    @overload
    def __rsub__(self, other: FloatArg) -> FloatForm: ...
    def __rsub__(self, other: IntArg | FloatArg) -> IntForm | FloatForm:
        from nu import Sub

        from .float_ import FloatForm

        if isinstance(other, float):
            return FloatForm(Sub(other, self))
        return IntForm(Sub(other, self))

    @overload
    def __mul__(self, other: IntArg) -> IntForm: ...
    @overload
    def __mul__(self, other: FloatArg) -> FloatForm: ...
    def __mul__(self, other: IntArg | FloatArg) -> IntForm | FloatForm:
        from nu import Mul

        from .float_ import FloatForm

        if isinstance(other, (float, FloatForm)):
            return FloatForm(Mul(self, other))
        return IntForm(Mul(self, other))

    @overload
    def __rmul__(self, other: IntArg) -> IntForm: ...
    @overload
    def __rmul__(self, other: FloatArg) -> FloatForm: ...
    def __rmul__(self, other: IntArg | FloatArg) -> IntForm | FloatForm:
        from nu import Mul

        from .float_ import FloatForm

        if isinstance(other, float):
            return FloatForm(Mul(other, self))
        return IntForm(Mul(other, self))

    def __truediv__(self, other: IntArg | FloatArg) -> FloatForm:
        from nu import Div

        from .float_ import FloatForm

        return FloatForm(Div(self, other))

    def __rtruediv__(self, other: IntArg | FloatArg) -> FloatForm:
        from nu import Div

        from .float_ import FloatForm

        return FloatForm(Div(other, self))

    @overload
    def __floordiv__(self, other: IntArg) -> IntForm: ...
    @overload
    def __floordiv__(self, other: FloatArg) -> FloatForm: ...
    def __floordiv__(self, other: IntArg | FloatArg) -> IntForm | FloatForm:
        from nu import FloorDiv

        from .float_ import FloatForm

        if isinstance(other, (float, FloatForm)):
            return FloatForm(FloorDiv(self, other))
        return IntForm(FloorDiv(self, other))

    @overload
    def __rfloordiv__(self, other: IntArg) -> IntForm: ...
    @overload
    def __rfloordiv__(self, other: FloatArg) -> FloatForm: ...
    def __rfloordiv__(self, other: IntArg | FloatArg) -> IntForm | FloatForm:
        from nu import FloorDiv

        from .float_ import FloatForm

        if isinstance(other, float):
            return FloatForm(FloorDiv(other, self))
        return IntForm(FloorDiv(other, self))

    @overload
    def __mod__(self, other: IntArg) -> IntForm: ...
    @overload
    def __mod__(self, other: FloatArg) -> FloatForm: ...
    def __mod__(self, other: IntArg | FloatArg) -> IntForm | FloatForm:
        from nu import Mod

        from .float_ import FloatForm

        if isinstance(other, (float, FloatForm)):
            return FloatForm(Mod(self, other))
        return IntForm(Mod(self, other))

    @overload
    def __rmod__(self, other: IntArg) -> IntForm: ...
    @overload
    def __rmod__(self, other: FloatArg) -> FloatForm: ...
    def __rmod__(self, other: IntArg | FloatArg) -> IntForm | FloatForm:
        from nu import Mod

        from .float_ import FloatForm

        if isinstance(other, float):
            return FloatForm(Mod(other, self))
        return IntForm(Mod(other, self))

    @overload
    def __pow__(self, other: IntArg) -> IntForm: ...
    @overload
    def __pow__(self, other: FloatArg) -> FloatForm: ...
    def __pow__(self, other: IntArg | FloatArg) -> IntForm | FloatForm:
        from nu import Pow

        from .float_ import FloatForm

        if isinstance(other, (float, FloatForm)):
            return FloatForm(Pow(self, other))
        return IntForm(Pow(self, other))

    @overload
    def __rpow__(self, other: IntArg) -> IntForm: ...
    @overload
    def __rpow__(self, other: FloatArg) -> FloatForm: ...
    def __rpow__(self, other: IntArg | FloatArg) -> IntForm | FloatForm:
        from nu import Pow

        from .float_ import FloatForm

        if isinstance(other, float):
            return FloatForm(Pow(other, self))
        return IntForm(Pow(other, self))

    def __neg__(self) -> IntForm:
        from nu import Neg

        return IntForm(Neg(self))

    def __pos__(self) -> IntForm:
        from nu import Pos

        return IntForm(Pos(self))

    def __abs__(self) -> IntForm:
        from nu import Abs

        return IntForm(Abs(self))

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

    def and_(self, other: BoolArg | IntArg) -> BoolForm:
        from nu import And

        from .bool_ import BoolForm

        return BoolForm(And(self, other))

    def or_(self, other: BoolArg | IntArg) -> BoolForm:
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

    # =========================================================================
    # BITWISE
    # =========================================================================

    def bitand(self, other: IntArg) -> IntForm:
        from nu import BitwiseAnd

        return IntForm(BitwiseAnd(self, other))

    def bitor(self, other: IntArg) -> IntForm:
        from nu import BitwiseOr

        return IntForm(BitwiseOr(self, other))

    def __xor__(self, other: IntArg) -> IntForm:
        from nu import Xor

        return IntForm(Xor(self, other))

    def __rxor__(self, other: IntArg) -> IntForm:
        from nu import Xor

        return IntForm(Xor(other, self))

    def bitnot(self) -> IntForm:
        from nu import BitwiseNot

        return IntForm(BitwiseNot(self))

    def __lshift__(self, other: IntArg) -> IntForm:
        from nu import LShift

        return IntForm(LShift(self, other))

    def __rlshift__(self, other: IntArg) -> IntForm:
        from nu import LShift

        return IntForm(LShift(other, self))

    def __rshift__(self, other: IntArg) -> IntForm:
        from nu import RShift

        return IntForm(RShift(self, other))

    def __rrshift__(self, other: IntArg) -> IntForm:
        from nu import RShift

        return IntForm(RShift(other, self))
