"""FloatForm - float interface."""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.lang import Form, TypedNu


if TYPE_CHECKING:
    from nu.lang import BoolArg, FloatArg, IntArg

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
        from nu.core import AddQuery

        return FloatForm(AddQuery(self, other))

    def __radd__(self, other: IntArg | FloatArg) -> FloatForm:
        from nu.core import AddQuery

        return FloatForm(AddQuery(other, self))

    def __sub__(self, other: IntArg | FloatArg) -> FloatForm:
        from nu.core import SubQuery

        return FloatForm(SubQuery(self, other))

    def __rsub__(self, other: IntArg | FloatArg) -> FloatForm:
        from nu.core import SubQuery

        return FloatForm(SubQuery(other, self))

    def __mul__(self, other: IntArg | FloatArg) -> FloatForm:
        from nu.core import MulQuery

        return FloatForm(MulQuery(self, other))

    def __rmul__(self, other: IntArg | FloatArg) -> FloatForm:
        from nu.core import MulQuery

        return FloatForm(MulQuery(other, self))

    def __truediv__(self, other: IntArg | FloatArg) -> FloatForm:
        from nu.core import DivQuery

        return FloatForm(DivQuery(self, other))

    def __rtruediv__(self, other: IntArg | FloatArg) -> FloatForm:
        from nu.core import DivQuery

        return FloatForm(DivQuery(other, self))

    def __floordiv__(self, other: IntArg | FloatArg) -> FloatForm:
        from nu.core import FloorDivQuery

        return FloatForm(FloorDivQuery(self, other))

    def __rfloordiv__(self, other: IntArg | FloatArg) -> FloatForm:
        from nu.core import FloorDivQuery

        return FloatForm(FloorDivQuery(other, self))

    def __mod__(self, other: IntArg | FloatArg) -> FloatForm:
        from nu.core import ModQuery

        return FloatForm(ModQuery(self, other))

    def __rmod__(self, other: IntArg | FloatArg) -> FloatForm:
        from nu.core import ModQuery

        return FloatForm(ModQuery(other, self))

    def __pow__(self, other: IntArg | FloatArg) -> FloatForm:
        from nu.core import PowQuery

        return FloatForm(PowQuery(self, other))

    def __rpow__(self, other: IntArg | FloatArg) -> FloatForm:
        from nu.core import PowQuery

        return FloatForm(PowQuery(other, self))

    def __neg__(self) -> FloatForm:
        from nu.core import NegQuery

        return FloatForm(NegQuery(self))

    def __pos__(self) -> FloatForm:
        from nu.core import PosQuery

        return FloatForm(PosQuery(self))

    def __abs__(self) -> FloatForm:
        from nu.core import AbsQuery

        return FloatForm(AbsQuery(self))

    # =========================================================================
    # COMPARISON
    # =========================================================================

    def __gt__(self, other: IntArg | FloatArg) -> BoolForm:
        from nu.core import GtQuery

        from .bool_ import BoolForm

        return BoolForm(GtQuery(self, other))

    def __lt__(self, other: IntArg | FloatArg) -> BoolForm:
        from nu.core import LtQuery

        from .bool_ import BoolForm

        return BoolForm(LtQuery(self, other))

    def __ge__(self, other: IntArg | FloatArg) -> BoolForm:
        from nu.core import GeQuery

        from .bool_ import BoolForm

        return BoolForm(GeQuery(self, other))

    def __le__(self, other: IntArg | FloatArg) -> BoolForm:
        from nu.core import LeQuery

        from .bool_ import BoolForm

        return BoolForm(LeQuery(self, other))

    __hash__ = object.__hash__

    def __eq__(self, other: IntArg | FloatArg) -> BoolForm:  # type: ignore[override]
        from nu.core import EqQuery

        from .bool_ import BoolForm

        return BoolForm(EqQuery(self, other))

    def __ne__(self, other: IntArg | FloatArg) -> BoolForm:  # type: ignore[override]
        from nu.core import NeQuery

        from .bool_ import BoolForm

        return BoolForm(NeQuery(self, other))

    def is_(self, other: IntArg | FloatArg) -> BoolForm:
        """Identity comparison: self is other."""
        from nu.core import IsQuery

        from .bool_ import BoolForm

        return BoolForm(IsQuery(self, other))

    # =========================================================================
    # LOGICAL
    # =========================================================================

    def and_(self, other: BoolArg | FloatArg) -> BoolForm:
        """Logical AND: self AND other."""
        from nu.core import AndQuery

        from .bool_ import BoolForm

        return BoolForm(AndQuery(self, other))

    def or_(self, other: BoolArg | FloatArg) -> BoolForm:
        """Logical OR: self OR other."""
        from nu.core import OrQuery

        from .bool_ import BoolForm

        return BoolForm(OrQuery(self, other))

    def not_(self) -> BoolForm:
        """Logical NOT: NOT self."""
        from nu.core import NotQuery

        from .bool_ import BoolForm

        return BoolForm(NotQuery(self))

    def bool_(self) -> BoolForm:
        """Convert to boolean."""
        from nu.core import BoolQuery

        from .bool_ import BoolForm

        return BoolForm(BoolQuery(self))
