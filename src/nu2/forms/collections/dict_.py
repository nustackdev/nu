"""DictForm - dict interface."""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu2.lang import TypedNu

from .abc import MutableMappingForm


if TYPE_CHECKING:
    from nu2.lang import DictArg, Nu

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
        from nu2.core import Gt

        from ..primitives import BoolForm

        return BoolForm(Gt(self, other))

    def __lt__(self, other: DictArg[K, V]) -> BoolForm:
        from nu2.core import Lt

        from ..primitives import BoolForm

        return BoolForm(Lt(self, other))

    def __ge__(self, other: DictArg[K, V]) -> BoolForm:
        from nu2.core import Ge

        from ..primitives import BoolForm

        return BoolForm(Ge(self, other))

    def __le__(self, other: DictArg[K, V]) -> BoolForm:
        from nu2.core import Le

        from ..primitives import BoolForm

        return BoolForm(Le(self, other))

    __hash__ = object.__hash__

    def __eq__(self, other: DictArg[K, V]) -> BoolForm:  # type: ignore[override]
        from nu2.core import Eq

        from ..primitives import BoolForm

        return BoolForm(Eq(self, other))

    def __ne__(self, other: DictArg[K, V]) -> BoolForm:  # type: ignore[override]
        from nu2.core import Ne

        from ..primitives import BoolForm

        return BoolForm(Ne(self, other))

    def is_(self, other: DictArg[K, V]) -> BoolForm:
        """Identity comparison: self is other."""
        from nu2.core import Is

        from ..primitives import BoolForm

        return BoolForm(Is(self, other))
