# ruff: noqa: D102
"""PV sequence reference — document model + PV substrate."""

from __future__ import annotations

from typing import TYPE_CHECKING, Self

from pv.collections import MutableSequenceView

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
from everyshape import ReactiveSequenceRefBase, Shape, Slot

from .base import ViewRef
from .items import ListItemRef


if TYPE_CHECKING:
    from pv.loc import path

    from everyabc import Sentinel, Term, Value


def _value_type_for(python_type: type) -> type[Value]:
    """Map Python type to its corresponding Value type."""
    mapping: dict[type, type] = {
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


class ListRef[
    T,
    ItemValueT,
](
    ReactiveSequenceRefBase[
        T,
        ListValue[T],
        ItemValueT,
    ],
    ViewRef[
        list[T],
        MutableSequenceView,
    ],
):
    """PV sequence reference — document model + PV substrate.

    Operations work lazily on PV views without loading into memory.
    """

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
        address: path.PathAddress | Term,
        item_type: type[T],
        item_value_type: type[ItemValueT],
        view_type: type[MutableSequenceView],
        parent: ViewRef | None = None,
        shape: type[Shape] | None = None,
    ) -> None:
        """Initialize sequence reference."""
        super().__init__(address, view_type, parent, shape)
        self.item_type = item_type
        self.item_value_type = item_value_type

    def _create_item_ref(
        self, index: int | Sentinel | Term[int | Sentinel]
    ) -> ListItemRef[T, ItemValueT]:
        """Create a reference to an item at the given index."""
        return ListItemRef(
            address=ensure_term(index),
            value_type=self.item_type,
            value_value_type=self.item_value_type,
            parent=self,
            shape=self._shape,
        )

    @classmethod
    def slot(
        cls,
        item_type: type[T],
        view_type: type[MutableSequenceView] | None = None,
    ) -> Self:
        """Create a slot for this list ref type.

        Args:
            item_type: Python type of items (primitives)
            view_type: View class implementing MutableSequenceView protocol

        Returns:
            Slot configured to create ListRef instances
        """
        from every_pv.views import ListView

        return Slot(
            cls,
            item_type=item_type,
            item_value_type=_value_type_for(item_type),
            view_type=view_type or ListView,
        )  # type: ignore
