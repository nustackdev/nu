"""SetForm, FrozenSetForm - set interfaces."""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu2.lang import TypedNu

from .abc import MutableSetForm, SetLikeForm


if TYPE_CHECKING:
    from nu2.lang import FrozenSetArg, Nu, SetArg

    from ..primitives import AnyForm, BoolForm
    from .list_ import ListForm


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
        """Wrap operand as SetForm."""
        return SetForm(operand)

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

    def __gt__(self, other: SetArg[T]) -> BoolForm:
        from nu2.core import Gt

        from ..primitives import BoolForm

        return BoolForm(Gt(self, other))

    def __lt__(self, other: SetArg[T]) -> BoolForm:
        from nu2.core import Lt

        from ..primitives import BoolForm

        return BoolForm(Lt(self, other))

    def __ge__(self, other: SetArg[T]) -> BoolForm:
        from nu2.core import Ge

        from ..primitives import BoolForm

        return BoolForm(Ge(self, other))

    def __le__(self, other: SetArg[T]) -> BoolForm:
        from nu2.core import Le

        from ..primitives import BoolForm

        return BoolForm(Le(self, other))

    __hash__ = object.__hash__

    def __eq__(self, other: SetArg[T]) -> BoolForm:  # type: ignore[override]
        from nu2.core import Eq

        from ..primitives import BoolForm

        return BoolForm(Eq(self, other))

    def __ne__(self, other: SetArg[T]) -> BoolForm:  # type: ignore[override]
        from nu2.core import Ne

        from ..primitives import BoolForm

        return BoolForm(Ne(self, other))

    def is_(self, other: SetArg[T]) -> BoolForm:
        """Identity comparison: self is other."""
        from nu2.core import Is

        from ..primitives import BoolForm

        return BoolForm(Is(self, other))


class FrozenSetForm[T](
    SetLikeForm[frozenset[T], T, "FrozenSetForm[T]", "AnyForm"],
    TypedNu[frozenset[T]],
):
    """FrozenSet interface. Immutable set + comparable."""

    def _wrap_set_result(self, operand: Nu) -> FrozenSetForm[T]:
        """Wrap operand as FrozenSetForm."""
        return FrozenSetForm(operand)

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

    def __gt__(self, other: FrozenSetArg[T]) -> BoolForm:
        from nu2.core import Gt

        from ..primitives import BoolForm

        return BoolForm(Gt(self, other))

    def __lt__(self, other: FrozenSetArg[T]) -> BoolForm:
        from nu2.core import Lt

        from ..primitives import BoolForm

        return BoolForm(Lt(self, other))

    def __ge__(self, other: FrozenSetArg[T]) -> BoolForm:
        from nu2.core import Ge

        from ..primitives import BoolForm

        return BoolForm(Ge(self, other))

    def __le__(self, other: FrozenSetArg[T]) -> BoolForm:
        from nu2.core import Le

        from ..primitives import BoolForm

        return BoolForm(Le(self, other))

    __hash__ = object.__hash__

    def __eq__(self, other: FrozenSetArg[T]) -> BoolForm:  # type: ignore[override]
        from nu2.core import Eq

        from ..primitives import BoolForm

        return BoolForm(Eq(self, other))

    def __ne__(self, other: FrozenSetArg[T]) -> BoolForm:  # type: ignore[override]
        from nu2.core import Ne

        from ..primitives import BoolForm

        return BoolForm(Ne(self, other))

    def is_(self, other: FrozenSetArg[T]) -> BoolForm:
        """Identity comparison: self is other."""
        from nu2.core import Is

        from ..primitives import BoolForm

        return BoolForm(Is(self, other))
