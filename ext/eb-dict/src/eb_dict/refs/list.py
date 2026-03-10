# ruff: noqa: D102
"""Dict sequence reference — ordered container backed by nested list."""

from __future__ import annotations

from typing import TYPE_CHECKING

from everybase.abc import (
    AnyValue,
    BoolValue,
    BytesValue,
    DictValue,
    FloatValue,
    IntValue,
    ListValue,
    SetValue,
    StrValue,
    ensure_term,
)
from everybase.shape import MutableSequenceRefBase, Slot

from .base import RefBase
from .items import ItemRef


if TYPE_CHECKING:
    from everybase import Sentinel, Term, Value


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

    def result(self, op: Term) -> ListValue[T]:
        return ListValue(op)

    def _wrap_iterable_result(self, operand: Term) -> ListValue[T]:
        return ListValue(operand)

    def _wrap_sliceable_result(self, operand: Term) -> ListValue[T]:
        return ListValue(operand)

    def _wrap_element_result(self, operand: Term) -> AnyValue:
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

    def _create_item_ref(self, index: int | Sentinel | Term[int | Sentinel]) -> ItemRef[T, ...]:
        return ItemRef(
            address=ensure_term(index),
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
