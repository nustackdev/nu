"""Dict view interfaces - DictKeysI, DictValuesI, DictItemsI."""

from __future__ import annotations

from collections.abc import ItemsView, KeysView, ValuesView
from typing import TYPE_CHECKING

from nu.interfaces.collections_abc import CollectionBase
from nu.interfaces.collections_abc.set_ import SetLikeBase
from nu.interfaces.interface import Interface


if TYPE_CHECKING:
    from nu.interfaces.special.any_ import AnyI
    from nu.terms import Nu

    from .list_ import ListI
    from .set_ import SetI


__all__ = [
    "DictItemsI",
    "DictKeysI",
    "DictValuesI",
]


class DictKeysI[K](
    SetLikeBase[KeysView[K], K, "SetI[K]", "AnyI"],
    Interface[KeysView[K]],
):
    """Dict key view interface - set-like, lazy, live."""

    def _wrap_set_result(self, operand: Nu) -> SetI[K]:
        from .set_ import SetI

        return SetI(operand)

    def _wrap_iterable_result(self, operand: Nu) -> ListI[K]:
        from .list_ import ListI

        return ListI(operand)

    def _wrap_element_result(self, operand: Nu) -> AnyI:
        from nu.interfaces.special.any_ import AnyI

        return AnyI(operand)

    def to_list(self) -> ListI[K]:
        from nu.ops.builtins.conversion import ToListOp

        from .list_ import ListI

        return ListI(ToListOp(self))

    def to_set(self) -> SetI[K]:
        from nu.ops.builtins.conversion import ToSetOp

        from .set_ import SetI

        return SetI(ToSetOp(self))


class DictValuesI[V](
    CollectionBase[V, "ListI[V]", "AnyI"],
    Interface[ValuesView[V]],
):
    """Dict value view interface - iterable, sized, containment."""

    def _wrap_iterable_result(self, operand: Nu) -> ListI[V]:
        from .list_ import ListI

        return ListI(operand)

    def _wrap_element_result(self, operand: Nu) -> AnyI:
        from nu.interfaces.special.any_ import AnyI

        return AnyI(operand)

    def to_list(self) -> ListI[V]:
        from nu.ops.builtins.conversion import ToListOp

        from .list_ import ListI

        return ListI(ToListOp(self))

    def to_set(self) -> SetI[V]:
        from nu.ops.builtins.conversion import ToSetOp

        from .set_ import SetI

        return SetI(ToSetOp(self))


class DictItemsI[K, V](
    SetLikeBase[ItemsView[K, V], tuple[K, V], "SetI[tuple[K, V]]", "AnyI"],
    Interface[ItemsView[K, V]],
):
    """Dict item view interface - set-like, lazy, live."""

    def _wrap_set_result(self, operand: Nu) -> SetI[tuple[K, V]]:
        from .set_ import SetI

        return SetI(operand)

    def _wrap_iterable_result(self, operand: Nu) -> ListI[tuple[K, V]]:
        from .list_ import ListI

        return ListI(operand)

    def _wrap_element_result(self, operand: Nu) -> AnyI:
        from nu.interfaces.special.any_ import AnyI

        return AnyI(operand)

    def to_list(self) -> ListI[tuple[K, V]]:
        from nu.ops.builtins.conversion import ToListOp

        from .list_ import ListI

        return ListI(ToListOp(self))

    def to_set(self) -> SetI[tuple[K, V]]:
        from nu.ops.builtins.conversion import ToSetOp

        from .set_ import SetI

        return SetI(ToSetOp(self))
