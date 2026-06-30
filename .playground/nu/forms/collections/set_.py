"""SetForm, FrozenSetForm - set interfaces."""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.terms import TypedNu

from .abc import MutableSetForm, SetLikeForm


if TYPE_CHECKING:
    from nu.forms.primitives import AnyForm, BoolForm
    from nu.terms import FrozenSetArg, Nu, SetArg


__all__ = [
    "FrozenSetForm",
    "SetForm",
]


class SetForm[T](
    MutableSetForm[set[T], T, "SetForm[T]", "AnyForm"],
    TypedNu[set[T]],
):
    """Set interface. Mutable set + comparable."""

    def _wrap_set_result(self, operand: Nu) -> SetForm[T]:
        return SetForm(operand)

    def _wrap_iterable_result(self, operand: Nu) -> ListForm:
        from .list_ import ListForm

        return ListForm(operand)

    def _wrap_element_result(self, operand: Nu) -> AnyForm:
        from nu.forms.primitives import AnyForm

        return AnyForm(operand)

    # =========================================================================
    # COMPARISON
    # =========================================================================

    def __gt__(self, other: SetArg[T]) -> BoolForm:
        from nu import Gt
        from nu.forms.primitives import BoolForm

        return BoolForm(Gt(self, other))

    def __lt__(self, other: SetArg[T]) -> BoolForm:
        from nu import Lt
        from nu.forms.primitives import BoolForm

        return BoolForm(Lt(self, other))

    def __ge__(self, other: SetArg[T]) -> BoolForm:
        from nu import Ge
        from nu.forms.primitives import BoolForm

        return BoolForm(Ge(self, other))

    def __le__(self, other: SetArg[T]) -> BoolForm:
        from nu import Le
        from nu.forms.primitives import BoolForm

        return BoolForm(Le(self, other))

    __hash__ = object.__hash__

    def __eq__(self, other: SetArg[T]) -> BoolForm:  # type: ignore[override]
        from nu import Eq
        from nu.forms.primitives import BoolForm

        return BoolForm(Eq(self, other))

    def __ne__(self, other: SetArg[T]) -> BoolForm:  # type: ignore[override]
        from nu import Ne
        from nu.forms.primitives import BoolForm

        return BoolForm(Ne(self, other))

    def is_(self, other: SetArg[T]) -> BoolForm:
        from nu import IdComp
        from nu.forms.primitives import BoolForm

        return BoolForm(IdComp(self, other))


class FrozenSetForm[T](
    SetLikeForm[frozenset[T], T, "FrozenSetForm[T]", "AnyForm"],
    TypedNu[frozenset[T]],
):
    """FrozenSet interface. Immutable set + comparable."""

    def _wrap_set_result(self, operand: Nu) -> FrozenSetForm[T]:
        return FrozenSetForm(operand)

    def _wrap_iterable_result(self, operand: Nu) -> ListForm:
        from .list_ import ListForm

        return ListForm(operand)

    def _wrap_element_result(self, operand: Nu) -> AnyForm:
        from nu.forms.primitives import AnyForm

        return AnyForm(operand)

    # =========================================================================
    # COMPARISON
    # =========================================================================

    def __gt__(self, other: FrozenSetArg[T]) -> BoolForm:
        from nu import Gt
        from nu.forms.primitives import BoolForm

        return BoolForm(Gt(self, other))

    def __lt__(self, other: FrozenSetArg[T]) -> BoolForm:
        from nu import Lt
        from nu.forms.primitives import BoolForm

        return BoolForm(Lt(self, other))

    def __ge__(self, other: FrozenSetArg[T]) -> BoolForm:
        from nu import Ge
        from nu.forms.primitives import BoolForm

        return BoolForm(Ge(self, other))

    def __le__(self, other: FrozenSetArg[T]) -> BoolForm:
        from nu import Le
        from nu.forms.primitives import BoolForm

        return BoolForm(Le(self, other))

    __hash__ = object.__hash__

    def __eq__(self, other: FrozenSetArg[T]) -> BoolForm:  # type: ignore[override]
        from nu import Eq
        from nu.forms.primitives import BoolForm

        return BoolForm(Eq(self, other))

    def __ne__(self, other: FrozenSetArg[T]) -> BoolForm:  # type: ignore[override]
        from nu import Ne
        from nu.forms.primitives import BoolForm

        return BoolForm(Ne(self, other))

    def is_(self, other: FrozenSetArg[T]) -> BoolForm:
        from nu import IdComp
        from nu.forms.primitives import BoolForm

        return BoolForm(IdComp(self, other))
