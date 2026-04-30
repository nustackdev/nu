# ruff: noqa: D102
"""Dict mapping reference — key-value container backed by nested dict."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from nu import (
    AnyForm,
    BoolForm,
    BytesForm,
    DictForm,
    DictItemsForm,
    DictKeysForm,
    DictValuesForm,
    FloatForm,
    IntForm,
    IteratorForm,
    ListForm,
    SetForm,
    StrForm,
)
from nu.shapes import MutableMappingRef, Slot
from nu.terms import Mode

from .base import RefBase
from .items import ItemRef


if TYPE_CHECKING:
    from nu import Form, Nu, Sentinel


def _value_type_for(python_type: type) -> type[Form]:
    """Map Python type to its corresponding Form."""
    mapping: dict[type, type[Form]] = {
        int: IntForm,
        str: StrForm,
        float: FloatForm,
        bool: BoolForm,
        bytes: BytesForm,
        list: ListForm,
        dict: DictForm,
        set: SetForm,
    }
    return mapping.get(python_type, AnyForm)


__all__ = [
    "DictRef",
]


class DictRef[K, V](
    MutableMappingRef[K, V, DictForm[K, V], AnyForm],
    RefBase[dict[K, V]],
):
    """Dict mapping reference — key-value container backed by nested dict."""

    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})

    def result(self, op: Nu) -> DictForm[K, V]:
        return DictForm(op)

    def _wrap_keys_result(self, operand: Nu) -> DictKeysForm:
        return DictKeysForm(operand)

    def _wrap_values_result(self, operand: Nu) -> DictValuesForm:
        return DictValuesForm(operand)

    def _wrap_items_result(self, operand: Nu) -> DictItemsForm:
        return DictItemsForm(operand)

    def _wrap_iterable_result(self, operand: Nu) -> IteratorForm:
        return IteratorForm(operand)

    def _wrap_value_result(self, operand: Nu) -> AnyForm:
        return AnyForm(operand)

    def _wrap_element_result(self, operand: Nu) -> AnyForm:
        return AnyForm(operand)

    def __init__(
        self,
        *,
        value_type: type[V],
        key_type: type[K],
        key_value_type: type,
        value_value_type: type,
        **kwargs: object,
    ) -> None:
        super().__init__(**kwargs)
        self.value_type = value_type
        self.key_type = key_type
        self.key_value_type = key_value_type
        self.value_value_type = value_value_type

    def _create_child_ref(self, key: K | Sentinel | Nu[K | Sentinel]) -> ItemRef[V, ...]:
        return ItemRef(
            address=key,
            value_type=self.value_type,
            value_value_type=self.value_value_type,
            parent=self,
            owner_shape=self._owner_shape,
        )

    @classmethod
    def slot[DK, DV](cls, value_type: type[DV], key_type: type[DK] = str) -> DictRef[DK, DV]:  # type: ignore[assignment]
        return Slot(
            cls,
            value_type=value_type,
            key_type=key_type,
            key_value_type=_value_type_for(key_type),
            value_value_type=_value_type_for(value_type),
        )  # type: ignore[return-value]
