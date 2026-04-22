"""DictI - dict interface."""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.terms import TypedNu

from .abc import MutableMappingI


if TYPE_CHECKING:
    from nu.primitives import AnyI, BoolI
    from nu.terms import DictArg, Nu

    from .views import DictItemsI, DictKeysI, DictValuesI


__all__ = [
    "DictI",
]


class DictI[K, V](
    MutableMappingI[dict[K, V], K, V, "DictI[K, V]", "AnyI"],
    TypedNu[dict[K, V]],
):
    """Dict interface. Mutable mapping + comparable."""

    def _wrap_keys_result(self, operand: Nu) -> DictKeysI:
        from .views import DictKeysI

        return DictKeysI(operand)

    def _wrap_values_result(self, operand: Nu) -> DictValuesI:
        from .views import DictValuesI

        return DictValuesI(operand)

    def _wrap_items_result(self, operand: Nu) -> DictItemsI:
        from .views import DictItemsI

        return DictItemsI(operand)

    def _wrap_value_result(self, operand: Nu) -> AnyI:
        from nu.primitives import AnyI

        return AnyI(operand)

    def _wrap_iterable_result(self, operand: Nu) -> ListI:
        from .list_ import ListI

        return ListI(operand)

    def _wrap_element_result(self, operand: Nu) -> AnyI:
        from nu.primitives import AnyI

        return AnyI(operand)

    def __getitem__(self, key: K) -> AnyI:
        from nu.interactions import At
        from nu.primitives import AnyI

        return AnyI(At(self, key))

    # =========================================================================
    # COMPARISON
    # =========================================================================

    def __gt__(self, other: DictArg[K, V]) -> BoolI:
        from nu.interactions import Gt
        from nu.primitives import BoolI

        return BoolI(Gt(self, other))

    def __lt__(self, other: DictArg[K, V]) -> BoolI:
        from nu.interactions import Lt
        from nu.primitives import BoolI

        return BoolI(Lt(self, other))

    def __ge__(self, other: DictArg[K, V]) -> BoolI:
        from nu.interactions import Ge
        from nu.primitives import BoolI

        return BoolI(Ge(self, other))

    def __le__(self, other: DictArg[K, V]) -> BoolI:
        from nu.interactions import Le
        from nu.primitives import BoolI

        return BoolI(Le(self, other))

    def eq(self, other: DictArg[K, V]) -> BoolI:
        from nu.interactions import Eq
        from nu.primitives import BoolI

        return BoolI(Eq(self, other))

    def ne(self, other: DictArg[K, V]) -> BoolI:
        from nu.interactions import Ne
        from nu.primitives import BoolI

        return BoolI(Ne(self, other))

    def is_(self, other: DictArg[K, V]) -> BoolI:
        from nu.interactions import IdComp
        from nu.primitives import BoolI

        return BoolI(IdComp(self, other))
