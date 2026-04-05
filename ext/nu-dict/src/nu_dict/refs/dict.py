# ruff: noqa: D102
"""Dict mapping reference — key-value container backed by nested dict."""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu import (
    AnyI,
    BoolI,
    BytesI,
    DictItemsI,
    DictKeysI,
    DictI,
    DictValuesI,
    FloatI,
    IntI,
    IteratorI,
    ListI,
    SetI,
    StrI,
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
        int: IntI,
        str: StrI,
        float: FloatI,
        bool: BoolI,
        bytes: BytesI,
        list: ListI,
        dict: DictI,
        set: SetI,
    }
    return mapping.get(python_type, AnyI)


__all__ = [
    "DictRef",
]


class DictRef[K, V](
    MutableMappingRefBase[K, V, DictI[K, V], AnyI],
    RefBase[dict[K, V]],
):
    """Dict mapping reference — key-value container backed by nested dict."""

    def result(self, op: Nu) -> DictI[K, V]:
        return DictI(op)

    def _wrap_keys_result(self, operand: Nu) -> DictKeysI:
        return DictKeysI(operand)

    def _wrap_values_result(self, operand: Nu) -> DictValuesI:
        return DictValuesI(operand)

    def _wrap_items_result(self, operand: Nu) -> DictItemsI:
        return DictItemsI(operand)

    def _wrap_iterable_result(self, operand: Nu) -> IteratorI:
        return IteratorI(operand)

    def _wrap_value_result(self, operand: Nu) -> AnyI:
        return AnyI(operand)

    def _wrap_element_result(self, operand: Nu) -> AnyI:
        return AnyI(operand)

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
