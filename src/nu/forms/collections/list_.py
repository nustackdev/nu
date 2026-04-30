"""ListForm - list interface."""

from __future__ import annotations

from typing import TYPE_CHECKING, overload

from nu.terms import TypedNu

from .abc import MutableSequenceForm


if TYPE_CHECKING:
    from nu.forms.primitives import AnyForm, BoolForm
    from nu.terms import IntArg, ListArg, Nu


__all__ = [
    "ListForm",
]


class ListForm[T](
    MutableSequenceForm[list[T], T, "ListForm[T]", "AnyForm"],
    TypedNu[list[T]],
):
    """List interface. Mutable sequence + comparable."""

    def _wrap_iterable_result(self, operand: Nu) -> ListForm:
        return ListForm(operand)

    def _wrap_sliceable_result(self, operand: Nu) -> ListForm:
        return ListForm(operand)

    def _wrap_element_result(self, operand: Nu) -> AnyForm:
        from nu.forms.primitives import AnyForm

        return AnyForm(operand)

    # =========================================================================
    # ARITHMETIC (concatenation)
    # =========================================================================

    def __add__(self, other: ListArg[T]) -> ListForm[T]:
        from nu import Add

        return ListForm(Add(self, other))

    def __radd__(self, other: ListArg[T]) -> ListForm[T]:
        from nu import Add

        return ListForm(Add(other, self))

    # =========================================================================
    # INDEXING / SLICING
    # =========================================================================

    @overload
    def __getitem__(self, key: IntArg) -> AnyForm: ...
    @overload
    def __getitem__(self, key: slice) -> ListForm[T]: ...
    def __getitem__(self, key: IntArg | slice) -> AnyForm | ListForm[T]:
        from nu import At, Slice
        from nu.forms.primitives import AnyForm

        if isinstance(key, slice):
            return ListForm(Slice(self, key.start, key.stop, key.step))
        return AnyForm(At(self, key))

    # =========================================================================
    # COMPARISON
    # =========================================================================

    def __gt__(self, other: ListArg[T]) -> BoolForm:
        from nu import Gt
        from nu.forms.primitives import BoolForm

        return BoolForm(Gt(self, other))

    def __lt__(self, other: ListArg[T]) -> BoolForm:
        from nu import Lt
        from nu.forms.primitives import BoolForm

        return BoolForm(Lt(self, other))

    def __ge__(self, other: ListArg[T]) -> BoolForm:
        from nu import Ge
        from nu.forms.primitives import BoolForm

        return BoolForm(Ge(self, other))

    def __le__(self, other: ListArg[T]) -> BoolForm:
        from nu import Le
        from nu.forms.primitives import BoolForm

        return BoolForm(Le(self, other))

    def eq(self, other: ListArg[T]) -> BoolForm:
        from nu import Eq
        from nu.forms.primitives import BoolForm

        return BoolForm(Eq(self, other))

    def ne(self, other: ListArg[T]) -> BoolForm:
        from nu import Ne
        from nu.forms.primitives import BoolForm

        return BoolForm(Ne(self, other))

    def is_(self, other: ListArg[T]) -> BoolForm:
        from nu import IdComp
        from nu.forms.primitives import BoolForm

        return BoolForm(IdComp(self, other))
