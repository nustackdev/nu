"""DictForm - dict interface."""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.terms import TypedNu

from .abc import MutableMappingForm


if TYPE_CHECKING:
    from nu.forms.primitives import AnyForm, BoolForm
    from nu.terms import DictArg, Nu

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
        from .views import DictKeysForm

        return DictKeysForm(operand)

    def _wrap_values_result(self, operand: Nu) -> DictValuesForm:
        from .views import DictValuesForm

        return DictValuesForm(operand)

    def _wrap_items_result(self, operand: Nu) -> DictItemsForm:
        from .views import DictItemsForm

        return DictItemsForm(operand)

    def _wrap_value_result(self, operand: Nu) -> AnyForm:
        from nu.forms.primitives import AnyForm

        return AnyForm(operand)

    def _wrap_iterable_result(self, operand: Nu) -> ListForm:
        from .list_ import ListForm

        return ListForm(operand)

    def _wrap_element_result(self, operand: Nu) -> AnyForm:
        from nu.forms.primitives import AnyForm

        return AnyForm(operand)

    # =========================================================================
    # COMPARISON
    # =========================================================================

    def __gt__(self, other: DictArg[K, V]) -> BoolForm:
        from nu import Gt
        from nu.forms.primitives import BoolForm

        return BoolForm(Gt(self, other))

    def __lt__(self, other: DictArg[K, V]) -> BoolForm:
        from nu import Lt
        from nu.forms.primitives import BoolForm

        return BoolForm(Lt(self, other))

    def __ge__(self, other: DictArg[K, V]) -> BoolForm:
        from nu import Ge
        from nu.forms.primitives import BoolForm

        return BoolForm(Ge(self, other))

    def __le__(self, other: DictArg[K, V]) -> BoolForm:
        from nu import Le
        from nu.forms.primitives import BoolForm

        return BoolForm(Le(self, other))

    __hash__ = object.__hash__

    def __eq__(self, other: DictArg[K, V]) -> BoolForm:  # type: ignore[override]
        from nu import Eq
        from nu.forms.primitives import BoolForm

        return BoolForm(Eq(self, other))

    def __ne__(self, other: DictArg[K, V]) -> BoolForm:  # type: ignore[override]
        from nu import Ne
        from nu.forms.primitives import BoolForm

        return BoolForm(Ne(self, other))

    def is_(self, other: DictArg[K, V]) -> BoolForm:
        from nu import IdComp
        from nu.forms.primitives import BoolForm

        return BoolForm(IdComp(self, other))
