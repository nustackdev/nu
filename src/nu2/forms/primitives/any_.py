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
    """Any/dynamic interface. Supports all interactions, results stay AnyForm."""

    # =========================================================================
    # ARITHMETIC
    # =========================================================================

    def __add__(self, other: object) -> AnyForm:
        from nu2.core import AddQuery

        return AnyForm(AddQuery(self, other))

    def __radd__(self, other: object) -> AnyForm:
        from nu2.core import AddQuery

        return AnyForm(AddQuery(other, self))

    def __sub__(self, other: object) -> AnyForm:
        from nu2.core import SubQuery

        return AnyForm(SubQuery(self, other))

    def __rsub__(self, other: object) -> AnyForm:
        from nu2.core import SubQuery

        return AnyForm(SubQuery(other, self))

    def __mul__(self, other: object) -> AnyForm:
        from nu2.core import MulQuery

        return AnyForm(MulQuery(self, other))

    def __rmul__(self, other: object) -> AnyForm:
        from nu2.core import MulQuery

        return AnyForm(MulQuery(other, self))

    def __truediv__(self, other: object) -> AnyForm:
        from nu2.core import DivQuery

        return AnyForm(DivQuery(self, other))

    def __rtruediv__(self, other: object) -> AnyForm:
        from nu2.core import DivQuery

        return AnyForm(DivQuery(other, self))

    def __floordiv__(self, other: object) -> AnyForm:
        from nu2.core import FloorDivQuery

        return AnyForm(FloorDivQuery(self, other))

    def __rfloordiv__(self, other: object) -> AnyForm:
        from nu2.core import FloorDivQuery

        return AnyForm(FloorDivQuery(other, self))

    def __mod__(self, other: object) -> AnyForm:
        from nu2.core import ModQuery

        return AnyForm(ModQuery(self, other))

    def __rmod__(self, other: object) -> AnyForm:
        from nu2.core import ModQuery

        return AnyForm(ModQuery(other, self))

    def __pow__(self, other: object) -> AnyForm:
        from nu2.core import PowQuery

        return AnyForm(PowQuery(self, other))

    def __rpow__(self, other: object) -> AnyForm:
        from nu2.core import PowQuery

        return AnyForm(PowQuery(other, self))

    def __neg__(self) -> AnyForm:
        from nu2.core import NegQuery

        return AnyForm(NegQuery(self))

    def __pos__(self) -> AnyForm:
        from nu2.core import PosQuery

        return AnyForm(PosQuery(self))

    def __abs__(self) -> AnyForm:
        from nu2.core import AbsQuery

        return AnyForm(AbsQuery(self))

    # =========================================================================
    # COMPARISON
    # =========================================================================

    def __gt__(self, other: object) -> BoolForm:
        from nu2.core import GtQuery

        from .bool_ import BoolForm

        return BoolForm(GtQuery(self, other))

    def __lt__(self, other: object) -> BoolForm:
        from nu2.core import LtQuery

        from .bool_ import BoolForm

        return BoolForm(LtQuery(self, other))

    def __ge__(self, other: object) -> BoolForm:
        from nu2.core import GeQuery

        from .bool_ import BoolForm

        return BoolForm(GeQuery(self, other))

    def __le__(self, other: object) -> BoolForm:
        from nu2.core import LeQuery

        from .bool_ import BoolForm

        return BoolForm(LeQuery(self, other))

    __hash__ = object.__hash__

    def __eq__(self, other: object) -> BoolForm:  # type: ignore[override]
        from nu2.core import EqQuery

        from .bool_ import BoolForm

        return BoolForm(EqQuery(self, other))

    def __ne__(self, other: object) -> BoolForm:  # type: ignore[override]
        from nu2.core import NeQuery

        from .bool_ import BoolForm

        return BoolForm(NeQuery(self, other))

    def is_(self, other: object) -> BoolForm:
        """Identity comparison: self is other."""
        from nu2.core import IsQuery

        from .bool_ import BoolForm

        return BoolForm(IsQuery(self, other))

    # =========================================================================
    # LOGICAL
    # =========================================================================

    def and_(self, other: object) -> BoolForm:
        """Logical AND: self AND other."""
        from nu2.core import AndQuery

        from .bool_ import BoolForm

        return BoolForm(AndQuery(self, other))

    def or_(self, other: object) -> BoolForm:
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

    def bitand(self, other: object) -> AnyForm:
        """Bitwise AND: self & other."""
        from nu2.core import BitAndQuery

        return AnyForm(BitAndQuery(self, other))

    def bitor(self, other: object) -> AnyForm:
        """Bitwise OR: self | other."""
        from nu2.core import BitOrQuery

        return AnyForm(BitOrQuery(self, other))

    def __xor__(self, other: object) -> AnyForm:
        from nu2.core import BitXorQuery

        return AnyForm(BitXorQuery(self, other))

    def __rxor__(self, other: object) -> AnyForm:
        from nu2.core import BitXorQuery

        return AnyForm(BitXorQuery(other, self))

    def bitnot(self) -> AnyForm:
        """Bitwise NOT: ~self."""
        from nu2.core import BitNotQuery

        return AnyForm(BitNotQuery(self))

    def __lshift__(self, other: object) -> AnyForm:
        from nu2.core import LShiftQuery

        return AnyForm(LShiftQuery(self, other))

    def __rshift__(self, other: object) -> AnyForm:
        from nu2.core import RShiftQuery

        return AnyForm(RShiftQuery(self, other))
