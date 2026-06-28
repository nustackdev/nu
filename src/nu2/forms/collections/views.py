"""Dict view interfaces - DictKeysForm, DictValuesForm, DictItemsForm."""

from __future__ import annotations

from collections.abc import ItemsView, KeysView, ValuesView
from typing import TYPE_CHECKING

from nu2.lang import TypedNu

from .abc import CollectionForm
from .abc.set_ import SetLikeForm


if TYPE_CHECKING:
    from nu2.lang import Nu

    from ..primitives import AnyForm
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
        """Wrap operand as SetForm."""
        from .set_ import SetForm

        return SetForm(operand)

    def _wrap_iterable_result(self, operand: Nu) -> ListForm[K]:
        """Wrap operand as ListForm."""
        from .list_ import ListForm

        return ListForm(operand)

    def _wrap_element_result(self, operand: Nu) -> AnyForm:
        """Wrap operand as AnyForm element."""
        from ..primitives import AnyForm

        return AnyForm(operand)

    def to_list(self) -> ListForm[K]:
        """Materialize keys view into a list."""
        from nu2.core import ListQuery

        from .list_ import ListForm

        return ListForm(ListQuery(self))

    def to_set(self) -> SetForm[K]:
        """Materialize keys view into a set."""
        from nu2.core import SetQuery

        from .set_ import SetForm

        return SetForm(SetQuery(self))


class DictValuesForm[V](
    CollectionForm[V, "ListForm[V]", "AnyForm"],
    TypedNu[ValuesView[V]],
):
    """Dict value view interface - iterable, sized, containment."""

    def _wrap_iterable_result(self, operand: Nu) -> ListForm[V]:
        """Wrap operand as ListForm."""
        from .list_ import ListForm

        return ListForm(operand)

    def _wrap_element_result(self, operand: Nu) -> AnyForm:
        """Wrap operand as AnyForm element."""
        from ..primitives import AnyForm

        return AnyForm(operand)

    def to_list(self) -> ListForm[V]:
        """Materialize values view into a list."""
        from nu2.core import ListQuery

        from .list_ import ListForm

        return ListForm(ListQuery(self))

    def to_set(self) -> SetForm[V]:
        """Materialize values view into a set."""
        from nu2.core import SetQuery

        from .set_ import SetForm

        return SetForm(SetQuery(self))


class DictItemsForm[K, V](
    SetLikeForm[ItemsView[K, V], tuple[K, V], "SetForm[tuple[K, V]]", "AnyForm"],
    TypedNu[ItemsView[K, V]],
):
    """Dict item view interface - set-like, lazy, live."""

    def _wrap_set_result(self, operand: Nu) -> SetForm[tuple[K, V]]:
        """Wrap operand as SetForm."""
        from .set_ import SetForm

        return SetForm(operand)

    def _wrap_iterable_result(self, operand: Nu) -> ListForm[tuple[K, V]]:
        """Wrap operand as ListForm."""
        from .list_ import ListForm

        return ListForm(operand)

    def _wrap_element_result(self, operand: Nu) -> AnyForm:
        """Wrap operand as AnyForm element."""
        from ..primitives import AnyForm

        return AnyForm(operand)

    def to_list(self) -> ListForm[tuple[K, V]]:
        """Materialize items view into a list."""
        from nu2.core import ListQuery

        from .list_ import ListForm

        return ListForm(ListQuery(self))

    def to_set(self) -> SetForm[tuple[K, V]]:
        """Materialize items view into a set."""
        from nu2.core import SetQuery

        from .set_ import SetForm

        return SetForm(SetQuery(self))
