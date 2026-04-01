# ruff: noqa: D102
"""Dict mapping reference — key-value container backed by nested dict."""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu import (
    AnyValue,
    BoolValue,
    BytesValue,
    DictItemsValue,
    DictKeysValue,
    DictValue,
    DictValuesValue,
    FloatValue,
    IntValue,
    IteratorValue,
    ListValue,
    SetValue,
    StrValue,
    ensure_nu,
)
from nu.shapes import MutableMappingRefBase, Slot

from .base import RefBase
from .items import ItemRef


if TYPE_CHECKING:
    from nu import Sentinel, Nu, Value


def _value_type_for(python_type: type) -> type[Value]:
    """Map Python type to its corresponding Value type."""
    mapping: dict[type, type[Value]] = {
        int: IntValue,
        str: StrValue,
        float: FloatValue,
        bool: BoolValue,
        bytes: BytesValue,
        list: ListValue,
        dict: DictValue,
        set: SetValue,
    }
    return mapping.get(python_type, AnyValue)


__all__ = [
    "DictRef",
]


class DictRef[K, V](
    MutableMappingRefBase[K, V, DictValue[K, V], AnyValue],
    RefBase[dict[K, V]],
):
    """Dict mapping reference — key-value container backed by nested dict."""

    def result(self, op: Nu) -> DictValue[K, V]:
        return DictValue(op)

    def _wrap_keys_result(self, operand: Nu) -> DictKeysValue:
        return DictKeysValue(operand)

    def _wrap_values_result(self, operand: Nu) -> DictValuesValue:
        return DictValuesValue(operand)

    def _wrap_items_result(self, operand: Nu) -> DictItemsValue:
        return DictItemsValue(operand)

    def _wrap_iterable_result(self, operand: Nu) -> IteratorValue:
        return IteratorValue(operand)

    def _wrap_value_result(self, operand: Nu) -> AnyValue:
        return AnyValue(operand)

    def _wrap_element_result(self, operand: Nu) -> AnyValue:
        return AnyValue(operand)

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
            address=ensure_nu(key),
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
