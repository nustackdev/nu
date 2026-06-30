"""DictForm - dict interface."""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.lang import TypedNu

from .abc import MutableMappingForm


if TYPE_CHECKING:
    from nu.lang import DictArg, Nu

    from ..primitives import AnyForm, BoolForm
    from .list_ import ListForm
    from .views import DictItemsForm, DictKeysForm, DictValuesForm


__all__ = [
    "DictForm",
]


class DictForm[K, V](
    MutableMappingForm[dict[K, V], K, V, "DictForm[K, V]", "AnyForm"],
    TypedNu[dict[K, V]],
):
    """Dict interface. Mutable mapping + comparable."""

    def _wrap_keys_result(self, operand: Nu) -> DictKeysForm:
        """Wrap operand as DictKeysForm."""
        from .views import DictKeysForm

        return DictKeysForm(operand)

    def _wrap_values_result(self, operand: Nu) -> DictValuesForm:
        """Wrap operand as DictValuesForm."""
        from .views import DictValuesForm

        return DictValuesForm(operand)

    def _wrap_items_result(self, operand: Nu) -> DictItemsForm:
        """Wrap operand as DictItemsForm."""
        from .views import DictItemsForm

        return DictItemsForm(operand)

    def _wrap_value_result(self, operand: Nu) -> AnyForm:
        """Wrap operand as AnyForm value."""
        from ..primitives import AnyForm

        return AnyForm(operand)

    def _wrap_mapping_result(self, operand: Nu) -> DictForm[K, V]:
        """Wrap operand as DictForm."""
        return DictForm(operand)

    def keys(self) -> DictKeysForm[K]:  # type: ignore[override]
        """Get all keys as a DictKeysForm."""
        from .abc.mapping_interactions import KeysQuery

        return self._wrap_keys_result(KeysQuery(self))

    def values(self) -> DictValuesForm[V]:  # type: ignore[override]
        """Get all values as a DictValuesForm."""
        from .abc.mapping_interactions import ValuesQuery

        return self._wrap_values_result(ValuesQuery(self))

    def items(self) -> DictItemsForm[K, V]:  # type: ignore[override]
        """Get all key-value pairs as a DictItemsForm."""
        from .abc.mapping_interactions import ItemsQuery

        return self._wrap_items_result(ItemsQuery(self))

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

    def __gt__(self, other: DictArg[K, V]) -> BoolForm:
        from nu.core import GtQuery

        from ..primitives import BoolForm

        return BoolForm(GtQuery(self, other))

    def __lt__(self, other: DictArg[K, V]) -> BoolForm:
        from nu.core import LtQuery

        from ..primitives import BoolForm

        return BoolForm(LtQuery(self, other))

    def __ge__(self, other: DictArg[K, V]) -> BoolForm:
        from nu.core import GeQuery

        from ..primitives import BoolForm

        return BoolForm(GeQuery(self, other))

    def __le__(self, other: DictArg[K, V]) -> BoolForm:
        from nu.core import LeQuery

        from ..primitives import BoolForm

        return BoolForm(LeQuery(self, other))

    __hash__ = object.__hash__

    def __eq__(self, other: DictArg[K, V]) -> BoolForm:  # type: ignore[override]
        from nu.core import EqQuery

        from ..primitives import BoolForm

        return BoolForm(EqQuery(self, other))

    def __ne__(self, other: DictArg[K, V]) -> BoolForm:  # type: ignore[override]
        from nu.core import NeQuery

        from ..primitives import BoolForm

        return BoolForm(NeQuery(self, other))

    def is_(self, other: DictArg[K, V]) -> BoolForm:
        """Identity comparison: self is other."""
        from nu.core import IsQuery

        from ..primitives import BoolForm

        return BoolForm(IsQuery(self, other))
