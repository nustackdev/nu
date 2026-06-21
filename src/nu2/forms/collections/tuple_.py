"""TupleForm - tuple interface."""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu2.lang import TypedNu

from .abc import SequenceForm


if TYPE_CHECKING:
    from nu2.lang import Nu, TupleArg

    from ..primitives import AnyForm, BoolForm
    from .list_ import ListForm


__all__ = [
    "TupleForm",
]


class TupleForm[*Ts](
    SequenceForm[tuple[*Ts], object, "ListForm[object]", "AnyForm"],
    TypedNu[tuple[*Ts]],
):
    """Tuple interface. Immutable sequence + comparable."""

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
    # COMPARISON
    # =========================================================================

    def __gt__(self, other: TupleArg[*Ts]) -> BoolForm:
        from nu2.core import Gt

        from ..primitives import BoolForm

        return BoolForm(Gt(self, other))

    def __lt__(self, other: TupleArg[*Ts]) -> BoolForm:
        from nu2.core import Lt

        from ..primitives import BoolForm

        return BoolForm(Lt(self, other))

    def __ge__(self, other: TupleArg[*Ts]) -> BoolForm:
        from nu2.core import Ge

        from ..primitives import BoolForm

        return BoolForm(Ge(self, other))

    def __le__(self, other: TupleArg[*Ts]) -> BoolForm:
        from nu2.core import Le

        from ..primitives import BoolForm

        return BoolForm(Le(self, other))

    __hash__ = object.__hash__

    def __eq__(self, other: TupleArg[*Ts]) -> BoolForm:  # type: ignore[override]
        from nu2.core import Eq

        from ..primitives import BoolForm

        return BoolForm(Eq(self, other))

    def __ne__(self, other: TupleArg[*Ts]) -> BoolForm:  # type: ignore[override]
        from nu2.core import Ne

        from ..primitives import BoolForm

        return BoolForm(Ne(self, other))

    def is_(self, other: TupleArg[*Ts]) -> BoolForm:
        """Identity comparison: self is other."""
        from nu2.core import Is

        from ..primitives import BoolForm

        return BoolForm(Is(self, other))
