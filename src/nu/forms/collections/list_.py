"""ListForm - list interface."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from nu.lang import TypedNu

from .abc import MutableSequenceForm
from .abc.sequence_interactions import ListCreate


if TYPE_CHECKING:
    from nu.lang import Arg, IntArg, ListArg, Nu

    from ..primitives import AnyForm, BoolForm


__all__ = [
    "ListForm",
]


class ListForm[T](
    MutableSequenceForm[list[T], T, "ListForm[T]", "AnyForm"],
    TypedNu[list[T]],
):
    """ListQuery interface. Mutable sequence + comparable."""

    @classmethod
    def create(cls) -> ListForm[T]:
        """Yield a fresh empty list."""
        return cls(ListCreate())

    def _wrap_iterable_result(self, operand: Nu) -> ListForm:
        """Wrap operand as ListForm."""
        return ListForm(operand)

    def _wrap_sliceable_result(self, operand: Nu) -> ListForm:
        """Wrap operand as ListForm for slice results."""
        return ListForm(operand)

    def _wrap_element_result(self, operand: Nu) -> AnyForm:
        """Wrap operand as AnyForm element."""
        from ..primitives import AnyForm

        return AnyForm(operand)

    # =========================================================================
    # ARITHMETIC (concatenation)
    # =========================================================================

    def __add__(self, other: ListArg[T]) -> ListForm[T]:
        from nu.core import AddQuery

        return ListForm(AddQuery(self, other))

    def __radd__(self, other: ListArg[T]) -> ListForm[T]:
        from nu.core import AddQuery

        return ListForm(AddQuery(other, self))

    def __iadd__(self, other: ListArg[T]) -> ListForm[T]:
        """In-place concat: self += other. Mutates and returns self (Action)."""
        from .abc.sequence_interactions import IAddAction

        return ListForm(IAddAction(self, other))

    def __mul__(self, n: IntArg) -> ListForm[T]:
        """Repeat: self * n -> new list (Query)."""
        from nu.core import MulQuery

        return ListForm(MulQuery(self, n))

    def __rmul__(self, n: IntArg) -> ListForm[T]:
        """Repeat: n * self -> new list (Query)."""
        from nu.core import MulQuery

        return ListForm(MulQuery(n, self))

    def __imul__(self, n: IntArg) -> ListForm[T]:
        """In-place repeat: self *= n. Mutates and returns self (Action)."""
        from .abc.sequence_interactions import IMulAction

        return ListForm(IMulAction(self, n))

    # =========================================================================
    # ITEM ACCESS (mutating)
    # =========================================================================

    def __setitem__(self, index: IntArg, value: Arg[T]) -> Any:  # noqa: ANN401
        """Subscript write: self[index] = value. Mutates; yields nothing (Command)."""
        from .abc.sequence_interactions import SetIndexCommand

        return SetIndexCommand(self, index, value)

    def __delitem__(self, index: IntArg) -> Any:  # noqa: ANN401
        """Subscript delete: del self[index]. Mutates; yields nothing (Command)."""
        from .abc.sequence_interactions import DelIndexCommand

        return DelIndexCommand(self, index)

    # =========================================================================
    # COMPARISON
    # =========================================================================

    def __gt__(self, other: ListArg[T]) -> BoolForm:
        from nu.core import GtQuery

        from ..primitives import BoolForm

        return BoolForm(GtQuery(self, other))

    def __lt__(self, other: ListArg[T]) -> BoolForm:
        from nu.core import LtQuery

        from ..primitives import BoolForm

        return BoolForm(LtQuery(self, other))

    def __ge__(self, other: ListArg[T]) -> BoolForm:
        from nu.core import GeQuery

        from ..primitives import BoolForm

        return BoolForm(GeQuery(self, other))

    def __le__(self, other: ListArg[T]) -> BoolForm:
        from nu.core import LeQuery

        from ..primitives import BoolForm

        return BoolForm(LeQuery(self, other))

    __hash__ = object.__hash__

    def __eq__(self, other: ListArg[T]) -> BoolForm:  # type: ignore[override]
        from nu.core import EqQuery

        from ..primitives import BoolForm

        return BoolForm(EqQuery(self, other))

    def __ne__(self, other: ListArg[T]) -> BoolForm:  # type: ignore[override]
        from nu.core import NeQuery

        from ..primitives import BoolForm

        return BoolForm(NeQuery(self, other))

    def is_(self, other: ListArg[T]) -> BoolForm:
        """Identity comparison: self is other."""
        from nu.core import IsQuery

        from ..primitives import BoolForm

        return BoolForm(IsQuery(self, other))
