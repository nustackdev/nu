"""DictI - dict interface."""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.interface import Interface

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
    Interface[dict[K, V]],
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
        from nu.ops import AtOp
        from nu.primitives import AnyI

        return AnyI(AtOp(self, key))

    # =========================================================================
    # COMPARISON
    # =========================================================================

    def __gt__(self, other: DictArg[K, V]) -> BoolI:
        from nu.ops import GtOp
        from nu.primitives import BoolI

        return BoolI(GtOp(self, other))

    def __lt__(self, other: DictArg[K, V]) -> BoolI:
        from nu.ops import LtOp
        from nu.primitives import BoolI

        return BoolI(LtOp(self, other))

    def __ge__(self, other: DictArg[K, V]) -> BoolI:
        from nu.ops import GeOp
        from nu.primitives import BoolI

        return BoolI(GeOp(self, other))

    def __le__(self, other: DictArg[K, V]) -> BoolI:
        from nu.ops import LeOp
        from nu.primitives import BoolI

        return BoolI(LeOp(self, other))

    def eq(self, other: DictArg[K, V]) -> BoolI:
        from nu.ops import EqOp
        from nu.primitives import BoolI

        return BoolI(EqOp(self, other))

    def ne(self, other: DictArg[K, V]) -> BoolI:
        from nu.ops import NeOp
        from nu.primitives import BoolI

        return BoolI(NeOp(self, other))

    def is_(self, other: DictArg[K, V]) -> BoolI:
        from nu.ops import IdCompOp
        from nu.primitives import BoolI

        return BoolI(IdCompOp(self, other))
