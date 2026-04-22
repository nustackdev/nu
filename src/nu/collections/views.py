"""Dict view interfaces - DictKeysI, DictValuesI, DictItemsI."""

from __future__ import annotations

from collections.abc import ItemsView, KeysView, ValuesView
from typing import TYPE_CHECKING

from nu.terms import TypedNu

from .abc import CollectionI
from .abc.set_ import SetLikeI


if TYPE_CHECKING:
    from nu.primitives import AnyI
    from nu.terms import Nu

    from .list_ import ListI
    from .set_ import SetI


__all__ = [
    "DictItemsI",
    "DictKeysI",
    "DictValuesI",
]


class DictKeysI[K](
    SetLikeI[KeysView[K], K, "SetI[K]", "AnyI"],
    TypedNu[KeysView[K]],
):
    """Dict key view interface - set-like, lazy, live."""

    def _wrap_set_result(self, operand: Nu) -> SetI[K]:
        from .set_ import SetI

        return SetI(operand)

    def _wrap_iterable_result(self, operand: Nu) -> ListI[K]:
        from .list_ import ListI

        return ListI(operand)

    def _wrap_element_result(self, operand: Nu) -> AnyI:
        from nu.primitives import AnyI

        return AnyI(operand)

    def to_list(self) -> ListI[K]:
        from nu.interactions import ToList

        from .list_ import ListI

        return ListI(ToList(self))

    def to_set(self) -> SetI[K]:
        from nu.interactions import ToSet

        from .set_ import SetI

        return SetI(ToSet(self))


class DictValuesI[V](
    CollectionI[V, "ListI[V]", "AnyI"],
    TypedNu[ValuesView[V]],
):
    """Dict value view interface - iterable, sized, containment."""

    def _wrap_iterable_result(self, operand: Nu) -> ListI[V]:
        from .list_ import ListI

        return ListI(operand)

    def _wrap_element_result(self, operand: Nu) -> AnyI:
        from nu.primitives import AnyI

        return AnyI(operand)

    def to_list(self) -> ListI[V]:
        from nu.interactions import ToList

        from .list_ import ListI

        return ListI(ToList(self))

    def to_set(self) -> SetI[V]:
        from nu.interactions import ToSet

        from .set_ import SetI

        return SetI(ToSet(self))


class DictItemsI[K, V](
    SetLikeI[ItemsView[K, V], tuple[K, V], "SetI[tuple[K, V]]", "AnyI"],
    TypedNu[ItemsView[K, V]],
):
    """Dict item view interface - set-like, lazy, live."""

    def _wrap_set_result(self, operand: Nu) -> SetI[tuple[K, V]]:
        from .set_ import SetI

        return SetI(operand)

    def _wrap_iterable_result(self, operand: Nu) -> ListI[tuple[K, V]]:
        from .list_ import ListI

        return ListI(operand)

    def _wrap_element_result(self, operand: Nu) -> AnyI:
        from nu.primitives import AnyI

        return AnyI(operand)

    def to_list(self) -> ListI[tuple[K, V]]:
        from nu.interactions import ToList

        from .list_ import ListI

        return ListI(ToList(self))

    def to_set(self) -> SetI[tuple[K, V]]:
        from nu.interactions import ToSet

        from .set_ import SetI

        return SetI(ToSet(self))
