# ruff: noqa: D102
"""Dict sequence reference — ordered container backed by nested list."""

from __future__ import annotations

from typing import TYPE_CHECKING

from everybase import (
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
from everyshape import MutableSequenceRefBase, Slot

from .base import RefBase
from .items import ItemRef


if TYPE_CHECKING:
    from typing import Self

    from everyabc import Sentinel, Term, Value
    from everyshape import Shape


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
    "SequenceRef",
]


class SequenceRef[T](
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
        address: str | int | Term,
        item_type: type[T],
        item_value_type: type,
        parent: RefBase | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        """Initialize sequence reference."""
        super().__init__(address, parent, owner_shape)
        self.item_type = item_type
        self.item_value_type = item_value_type

    def _create_item_ref(self, index: int | Sentinel | Term[int | Sentinel]) -> ItemRef[T, ...]:
        """Create a reference to the item at the given index."""
        return ItemRef(
            address=ensure_term(index),
            value_type=self.item_type,
            value_value_type=self.item_value_type,
            parent=self,
            owner_shape=self._owner_shape,
        )

    @classmethod
    def slot(cls, item_type: type[T]) -> Self:
        """Create a slot for this sequence ref type.

        Args:
            item_type: Python type of items.

        Returns:
            Slot that creates SequenceRef instances.
        """
        return Slot(
            cls,
            item_type=item_type,
            item_value_type=_value_type_for(item_type),
        )  # type: ignore[return-value]
