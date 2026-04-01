# ruff: noqa: D102
"""Dict sequence reference — ordered container backed by nested list."""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu import (
    AnyValue,
    BoolValue,
    BytesValue,
    DictValue,
    FloatValue,
    IntValue,
    IteratorValue,
    ListValue,
    SetValue,
    StrValue,
    ensure_nu,
)
from nu.shapes import MutableSequenceRefBase, Slot

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
    "ListRef",
]


class ListRef[T](
    MutableSequenceRefBase[T, ListValue[T], AnyValue],
    RefBase[list[T]],
):
    """Dict sequence reference — ordered container backed by nested list."""

    def result(self, op: Nu) -> ListValue[T]:
        return ListValue(op)

    def _wrap_iterable_result(self, operand: Nu) -> IteratorValue:
        return IteratorValue(operand)

    def _wrap_sliceable_result(self, operand: Nu) -> ListValue[T]:
        return ListValue(operand)  # slices stay materialized

    def _wrap_element_result(self, operand: Nu) -> AnyValue:
        return AnyValue(operand)

    def __init__(
        self,
        *,
        item_type: type[T],
        item_value_type: type,
        **kwargs: object,
    ) -> None:
        super().__init__(**kwargs)
        self.item_type = item_type
        self.item_value_type = item_value_type

    def _create_item_ref(self, index: int | Sentinel | Nu[int | Sentinel]) -> ItemRef[T, ...]:
        return ItemRef(
            address=ensure_nu(index),
            value_type=self.item_type,
            value_value_type=self.item_value_type,
            parent=self,
            owner_shape=self._owner_shape,
        )

    @classmethod
    def slot[E](cls, item_type: type[E]) -> ListRef[E]:
        return Slot(
            cls,
            item_type=item_type,
            item_value_type=_value_type_for(item_type),
        )  # type: ignore[return-value]
