"""IntForm - integer interface.

IntForm = Form[int] + arithmetic + comparison + logical + bitwise.
Handles int/float promotion: int op float -> FloatForm.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, overload

from nu2.lang import Form, TypedNu


if TYPE_CHECKING:
    from nu2.lang import BoolArg, FloatArg, IntArg

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
        from nu2.core import AddQuery

        from .float_ import FloatForm

        if isinstance(other, (float, FloatForm)):
            return FloatForm(AddQuery(self, other))
        return IntForm(AddQuery(self, other))

    @overload
    def __radd__(self, other: IntArg) -> IntForm: ...
    @overload
    def __radd__(self, other: FloatArg) -> FloatForm: ...
    def __radd__(self, other: IntArg | FloatArg) -> IntForm | FloatForm:
        from nu2.core import AddQuery

        from .float_ import FloatForm

        if isinstance(other, float):
            return FloatForm(AddQuery(other, self))
        return IntForm(AddQuery(other, self))

    @overload
    def __sub__(self, other: IntArg) -> IntForm: ...
    @overload
    def __sub__(self, other: FloatArg) -> FloatForm: ...
    def __sub__(self, other: IntArg | FloatArg) -> IntForm | FloatForm:
        from nu2.core import SubQuery

        from .float_ import FloatForm

        if isinstance(other, (float, FloatForm)):
            return FloatForm(SubQuery(self, other))
        return IntForm(SubQuery(self, other))

    @overload
    def __rsub__(self, other: IntArg) -> IntForm: ...
    @overload
    def __rsub__(self, other: FloatArg) -> FloatForm: ...
    def __rsub__(self, other: IntArg | FloatArg) -> IntForm | FloatForm:
        from nu2.core import SubQuery

        from .float_ import FloatForm

        if isinstance(other, float):
            return FloatForm(SubQuery(other, self))
        return IntForm(SubQuery(other, self))

    @overload
    def __mul__(self, other: IntArg) -> IntForm: ...
    @overload
    def __mul__(self, other: FloatArg) -> FloatForm: ...
    def __mul__(self, other: IntArg | FloatArg) -> IntForm | FloatForm:
        from nu2.core import MulQuery

        from .float_ import FloatForm

        if isinstance(other, (float, FloatForm)):
            return FloatForm(MulQuery(self, other))
        return IntForm(MulQuery(self, other))

    @overload
    def __rmul__(self, other: IntArg) -> IntForm: ...
    @overload
    def __rmul__(self, other: FloatArg) -> FloatForm: ...
    def __rmul__(self, other: IntArg | FloatArg) -> IntForm | FloatForm:
        from nu2.core import MulQuery

        from .float_ import FloatForm

        if isinstance(other, float):
            return FloatForm(MulQuery(other, self))
        return IntForm(MulQuery(other, self))

    def __truediv__(self, other: IntArg | FloatArg) -> FloatForm:
        from nu2.core import DivQuery

        from .float_ import FloatForm

        return FloatForm(DivQuery(self, other))

    def __rtruediv__(self, other: IntArg | FloatArg) -> FloatForm:
        from nu2.core import DivQuery

        from .float_ import FloatForm

        return FloatForm(DivQuery(other, self))

    @overload
    def __floordiv__(self, other: IntArg) -> IntForm: ...
    @overload
    def __floordiv__(self, other: FloatArg) -> FloatForm: ...
    def __floordiv__(self, other: IntArg | FloatArg) -> IntForm | FloatForm:
        from nu2.core import FloorDivQuery

        from .float_ import FloatForm

        if isinstance(other, (float, FloatForm)):
            return FloatForm(FloorDivQuery(self, other))
        return IntForm(FloorDivQuery(self, other))

    @overload
    def __rfloordiv__(self, other: IntArg) -> IntForm: ...
    @overload
    def __rfloordiv__(self, other: FloatArg) -> FloatForm: ...
    def __rfloordiv__(self, other: IntArg | FloatArg) -> IntForm | FloatForm:
        from nu2.core import FloorDivQuery

        from .float_ import FloatForm

        if isinstance(other, float):
            return FloatForm(FloorDivQuery(other, self))
        return IntForm(FloorDivQuery(other, self))

    @overload
    def __mod__(self, other: IntArg) -> IntForm: ...
    @overload
    def __mod__(self, other: FloatArg) -> FloatForm: ...
    def __mod__(self, other: IntArg | FloatArg) -> IntForm | FloatForm:
        from nu2.core import ModQuery

        from .float_ import FloatForm

        if isinstance(other, (float, FloatForm)):
            return FloatForm(ModQuery(self, other))
        return IntForm(ModQuery(self, other))

    @overload
    def __rmod__(self, other: IntArg) -> IntForm: ...
    @overload
    def __rmod__(self, other: FloatArg) -> FloatForm: ...
    def __rmod__(self, other: IntArg | FloatArg) -> IntForm | FloatForm:
        from nu2.core import ModQuery

        from .float_ import FloatForm

        if isinstance(other, float):
            return FloatForm(ModQuery(other, self))
        return IntForm(ModQuery(other, self))

    @overload
    def __pow__(self, other: IntArg) -> IntForm: ...
    @overload
    def __pow__(self, other: FloatArg) -> FloatForm: ...
    def __pow__(self, other: IntArg | FloatArg) -> IntForm | FloatForm:
        from nu2.core import PowQuery

        from .float_ import FloatForm

        if isinstance(other, (float, FloatForm)):
            return FloatForm(PowQuery(self, other))
        return IntForm(PowQuery(self, other))

    @overload
    def __rpow__(self, other: IntArg) -> IntForm: ...
    @overload
    def __rpow__(self, other: FloatArg) -> FloatForm: ...
    def __rpow__(self, other: IntArg | FloatArg) -> IntForm | FloatForm:
        from nu2.core import PowQuery

        from .float_ import FloatForm

        if isinstance(other, float):
            return FloatForm(PowQuery(other, self))
        return IntForm(PowQuery(other, self))

    def __neg__(self) -> IntForm:
        from nu2.core import NegQuery

        return IntForm(NegQuery(self))

    def __pos__(self) -> IntForm:
        from nu2.core import PosQuery

        return IntForm(PosQuery(self))

    def __abs__(self) -> IntForm:
        from nu2.core import AbsQuery

        return IntForm(AbsQuery(self))

    # =========================================================================
    # COMPARISON
    # =========================================================================

    def __gt__(self, other: IntArg | FloatArg) -> BoolForm:
        from nu2.core import GtQuery

        from .bool_ import BoolForm

        return BoolForm(GtQuery(self, other))

    def __lt__(self, other: IntArg | FloatArg) -> BoolForm:
        from nu2.core import LtQuery

        from .bool_ import BoolForm

        return BoolForm(LtQuery(self, other))

    def __ge__(self, other: IntArg | FloatArg) -> BoolForm:
        from nu2.core import GeQuery

        from .bool_ import BoolForm

        return BoolForm(GeQuery(self, other))

    def __le__(self, other: IntArg | FloatArg) -> BoolForm:
        from nu2.core import LeQuery

        from .bool_ import BoolForm

        return BoolForm(LeQuery(self, other))

    __hash__ = object.__hash__

    def __eq__(self, other: IntArg | FloatArg) -> BoolForm:  # type: ignore[override]
        from nu2.core import EqQuery

        from .bool_ import BoolForm

        return BoolForm(EqQuery(self, other))

    def __ne__(self, other: IntArg | FloatArg) -> BoolForm:  # type: ignore[override]
        from nu2.core import NeQuery

        from .bool_ import BoolForm

        return BoolForm(NeQuery(self, other))

    def is_(self, other: IntArg | FloatArg) -> BoolForm:
        """Identity comparison: self is other."""
        from nu2.core import IsQuery

        from .bool_ import BoolForm

        return BoolForm(IsQuery(self, other))

    # =========================================================================
    # LOGICAL
    # =========================================================================

    def and_(self, other: BoolArg | IntArg) -> BoolForm:
        """Logical AND: self AND other."""
        from nu2.core import AndQuery

        from .bool_ import BoolForm

        return BoolForm(AndQuery(self, other))

    def or_(self, other: BoolArg | IntArg) -> BoolForm:
        """Logical OR: self OR other."""
        from nu2.core import OrQuery

        from .bool_ import BoolForm

        return BoolForm(OrQuery(self, other))

    def not_(self) -> BoolForm:
        """Logical NOT: NOT self."""
        from nu2.core import NotQuery

        from .bool_ import BoolForm

        return BoolForm(NotQuery(self))

    def bool_(self) -> BoolForm:
        """Convert to boolean."""
        from nu2.core import BoolQuery

        from .bool_ import BoolForm

        return BoolForm(BoolQuery(self))

    # =========================================================================
    # BITWISE
    # =========================================================================

    def bitand(self, other: IntArg) -> IntForm:
        """Bitwise AND: self & other."""
        from nu2.core import BitAndQuery

        return IntForm(BitAndQuery(self, other))

    def bitor(self, other: IntArg) -> IntForm:
        """Bitwise OR: self | other."""
        from nu2.core import BitOrQuery

        return IntForm(BitOrQuery(self, other))

    def __xor__(self, other: IntArg) -> IntForm:
        from nu2.core import BitXorQuery

        return IntForm(BitXorQuery(self, other))

    def __rxor__(self, other: IntArg) -> IntForm:
        from nu2.core import BitXorQuery

        return IntForm(BitXorQuery(other, self))

    def bitnot(self) -> IntForm:
        """Bitwise NOT: ~self."""
        from nu2.core import BitNotQuery

        return IntForm(BitNotQuery(self))

    def __lshift__(self, other: IntArg) -> IntForm:
        from nu2.core import LShiftQuery

        return IntForm(LShiftQuery(self, other))

    def __rlshift__(self, other: IntArg) -> IntForm:
        from nu2.core import LShiftQuery

        return IntForm(LShiftQuery(other, self))

    def __rshift__(self, other: IntArg) -> IntForm:
        from nu2.core import RShiftQuery

        return IntForm(RShiftQuery(self, other))

    def __rrshift__(self, other: IntArg) -> IntForm:
        from nu2.core import RShiftQuery

        return IntForm(RShiftQuery(other, self))
