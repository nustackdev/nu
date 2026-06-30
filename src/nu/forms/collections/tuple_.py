"""TupleForm - tuple interface."""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.lang import TypedNu

from .abc import SequenceForm


if TYPE_CHECKING:
    from nu.lang import IntArg, Nu, TupleArg

    from ..primitives import AnyForm, BoolForm
    from .list_ import ListForm


__all__ = [
    "TupleForm",
]


class TupleForm[*Ts](
    SequenceForm[tuple[*Ts], object, "ListForm[object]", "AnyForm"],
    TypedNu[tuple[*Ts]],
):
    """TupleQuery interface. Immutable sequence + comparable."""

    def _wrap_sliceable_result(self, operand: Nu) -> TupleForm:
        """Wrap operand as TupleForm for slice results."""
        return TupleForm(operand)

    def _wrap_iterable_result(self, operand: Nu) -> ListForm:
        """Wrap operand as ListForm."""
        from .list_ import ListForm

        return ListForm(operand)

    def _wrap_element_result(self, operand: Nu) -> AnyForm:
        """Wrap operand as AnyForm element."""
        from ..primitives import AnyForm

        return AnyForm(operand)

    # =========================================================================
    # ARITHMETIC (concatenation / repeat) — new value, no mutation
    # =========================================================================

    def __add__(self, other: TupleArg[*Ts]) -> TupleForm:
        """Concat: self + other -> new tuple (Query)."""
        from nu.core import AddQuery

        return TupleForm(AddQuery(self, other))

    def __radd__(self, other: TupleArg[*Ts]) -> TupleForm:
        """Concat: other + self -> new tuple (Query)."""
        from nu.core import AddQuery

        return TupleForm(AddQuery(other, self))

    def __mul__(self, n: IntArg) -> TupleForm:
        """Repeat: self * n -> new tuple (Query)."""
        from nu.core import MulQuery

        return TupleForm(MulQuery(self, n))

    def __rmul__(self, n: IntArg) -> TupleForm:
        """Repeat: n * self -> new tuple (Query)."""
        from nu.core import MulQuery

        return TupleForm(MulQuery(n, self))

    # =========================================================================
    # COMPARISON
    # =========================================================================

    def __gt__(self, other: TupleArg[*Ts]) -> BoolForm:
        from nu.core import GtQuery

        from ..primitives import BoolForm

        return BoolForm(GtQuery(self, other))

    def __lt__(self, other: TupleArg[*Ts]) -> BoolForm:
        from nu.core import LtQuery

        from ..primitives import BoolForm

        return BoolForm(LtQuery(self, other))

    def __ge__(self, other: TupleArg[*Ts]) -> BoolForm:
        from nu.core import GeQuery

        from ..primitives import BoolForm

        return BoolForm(GeQuery(self, other))

    def __le__(self, other: TupleArg[*Ts]) -> BoolForm:
        from nu.core import LeQuery

        from ..primitives import BoolForm

        return BoolForm(LeQuery(self, other))

    __hash__ = object.__hash__

    def __eq__(self, other: TupleArg[*Ts]) -> BoolForm:  # type: ignore[override]
        from nu.core import EqQuery

        from ..primitives import BoolForm

        return BoolForm(EqQuery(self, other))

    def __ne__(self, other: TupleArg[*Ts]) -> BoolForm:  # type: ignore[override]
        from nu.core import NeQuery

        from ..primitives import BoolForm

        return BoolForm(NeQuery(self, other))

    def is_(self, other: TupleArg[*Ts]) -> BoolForm:
        """Identity comparison: self is other."""
        from nu.core import IsQuery

        from ..primitives import BoolForm

        return BoolForm(IsQuery(self, other))
