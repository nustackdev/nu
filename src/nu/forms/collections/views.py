"""Dict view interfaces - DictKeysForm, DictValuesForm, DictItemsForm."""

from __future__ import annotations

from collections.abc import ItemsView, KeysView, ValuesView
from typing import TYPE_CHECKING

from nu.terms import TypedNu

from .abc import CollectionForm
from .abc.set_ import SetLikeForm


if TYPE_CHECKING:
    from nu.forms.primitives import AnyForm
    from nu.terms import Nu

    from .list_ import ListForm
    from .set_ import SetForm


__all__ = [
    "DictItemsForm",
    "DictKeysForm",
    "DictValuesForm",
]


class DictKeysForm[K](
    SetLikeForm[KeysView[K], K, "SetForm[K]", "AnyForm"],
    TypedNu[KeysView[K]],
):
    """Dict key view interface - set-like, lazy, live."""

    def _wrap_set_result(self, operand: Nu) -> SetForm[K]:
        from .set_ import SetForm

        return SetForm(operand)

    def _wrap_iterable_result(self, operand: Nu) -> ListForm[K]:
        from .list_ import ListForm

        return ListForm(operand)

    def _wrap_element_result(self, operand: Nu) -> AnyForm:
        from nu.forms.primitives import AnyForm

        return AnyForm(operand)

    def to_list(self) -> ListForm[K]:
        from nu import ToList

        from .list_ import ListForm

        return ListForm(ToList(self))

    def to_set(self) -> SetForm[K]:
        from nu import ToSet

        from .set_ import SetForm

        return SetForm(ToSet(self))


class DictValuesForm[V](
    CollectionForm[V, "ListForm[V]", "AnyForm"],
    TypedNu[ValuesView[V]],
):
    """Dict value view interface - iterable, sized, containment."""

    def _wrap_iterable_result(self, operand: Nu) -> ListForm[V]:
        from .list_ import ListForm

        return ListForm(operand)

    def _wrap_element_result(self, operand: Nu) -> AnyForm:
        from nu.forms.primitives import AnyForm

        return AnyForm(operand)

    def to_list(self) -> ListForm[V]:
        from nu import ToList

        from .list_ import ListForm

        return ListForm(ToList(self))

    def to_set(self) -> SetForm[V]:
        from nu import ToSet

        from .set_ import SetForm

        return SetForm(ToSet(self))


class DictItemsForm[K, V](
    SetLikeForm[ItemsView[K, V], tuple[K, V], "SetForm[tuple[K, V]]", "AnyForm"],
    TypedNu[ItemsView[K, V]],
):
    """Dict item view interface - set-like, lazy, live."""

    def _wrap_set_result(self, operand: Nu) -> SetForm[tuple[K, V]]:
        from .set_ import SetForm

        return SetForm(operand)

    def _wrap_iterable_result(self, operand: Nu) -> ListForm[tuple[K, V]]:
        from .list_ import ListForm

        return ListForm(operand)

    def _wrap_element_result(self, operand: Nu) -> AnyForm:
        from nu.forms.primitives import AnyForm

        return AnyForm(operand)

    def to_list(self) -> ListForm[tuple[K, V]]:
        from nu import ToList

        from .list_ import ListForm

        return ListForm(ToList(self))

    def to_set(self) -> SetForm[tuple[K, V]]:
        from nu import ToSet

        from .set_ import SetForm

        return SetForm(ToSet(self))
