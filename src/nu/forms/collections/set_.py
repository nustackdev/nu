"""SetForm, FrozenSetForm - set interfaces."""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.lang import TypedNu

from .abc import MutableSetForm, SetLikeForm
from .abc.set_interactions import FrozenSetCreate, SetCreate


if TYPE_CHECKING:
    from nu.lang import FrozenSetArg, Nu, SetArg

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
    """SetQuery interface. Mutable set + comparable."""

    @classmethod
    def create(cls) -> SetForm[T]:
        """Yield a fresh empty set."""
        return cls(SetCreate())

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
        from nu.core import GtQuery

        from ..primitives import BoolForm

        return BoolForm(GtQuery(self, other))

    def __lt__(self, other: SetArg[T]) -> BoolForm:
        from nu.core import LtQuery

        from ..primitives import BoolForm

        return BoolForm(LtQuery(self, other))

    def __ge__(self, other: SetArg[T]) -> BoolForm:
        from nu.core import GeQuery

        from ..primitives import BoolForm

        return BoolForm(GeQuery(self, other))

    def __le__(self, other: SetArg[T]) -> BoolForm:
        from nu.core import LeQuery

        from ..primitives import BoolForm

        return BoolForm(LeQuery(self, other))

    __hash__ = object.__hash__

    def __eq__(self, other: SetArg[T]) -> BoolForm:  # type: ignore[override]
        from nu.core import EqQuery

        from ..primitives import BoolForm

        return BoolForm(EqQuery(self, other))

    def __ne__(self, other: SetArg[T]) -> BoolForm:  # type: ignore[override]
        from nu.core import NeQuery

        from ..primitives import BoolForm

        return BoolForm(NeQuery(self, other))

    def is_(self, other: SetArg[T]) -> BoolForm:
        """Identity comparison: self is other."""
        from nu.core import IsQuery

        from ..primitives import BoolForm

        return BoolForm(IsQuery(self, other))


class FrozenSetForm[T](
    SetLikeForm[frozenset[T], T, "FrozenSetForm[T]", "AnyForm"],
    TypedNu[frozenset[T]],
):
    """FrozenSet interface. Immutable set + comparable."""

    @classmethod
    def create(cls) -> FrozenSetForm[T]:
        """Yield an empty frozenset."""
        return cls(FrozenSetCreate())

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
        from nu.core import GtQuery

        from ..primitives import BoolForm

        return BoolForm(GtQuery(self, other))

    def __lt__(self, other: FrozenSetArg[T]) -> BoolForm:
        from nu.core import LtQuery

        from ..primitives import BoolForm

        return BoolForm(LtQuery(self, other))

    def __ge__(self, other: FrozenSetArg[T]) -> BoolForm:
        from nu.core import GeQuery

        from ..primitives import BoolForm

        return BoolForm(GeQuery(self, other))

    def __le__(self, other: FrozenSetArg[T]) -> BoolForm:
        from nu.core import LeQuery

        from ..primitives import BoolForm

        return BoolForm(LeQuery(self, other))

    __hash__ = object.__hash__

    def __eq__(self, other: FrozenSetArg[T]) -> BoolForm:  # type: ignore[override]
        from nu.core import EqQuery

        from ..primitives import BoolForm

        return BoolForm(EqQuery(self, other))

    def __ne__(self, other: FrozenSetArg[T]) -> BoolForm:  # type: ignore[override]
        from nu.core import NeQuery

        from ..primitives import BoolForm

        return BoolForm(NeQuery(self, other))

    def is_(self, other: FrozenSetArg[T]) -> BoolForm:
        """Identity comparison: self is other."""
        from nu.core import IsQuery

        from ..primitives import BoolForm

        return BoolForm(IsQuery(self, other))
