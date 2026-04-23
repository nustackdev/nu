# ruff: noqa: D102
"""PV sequence reference — document model + PV substrate."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from nu import (
    AnyI,
    BoolI,
    BytesI,
    DictI,
    FloatI,
    IntI,
    IteratorI,
    ListI,
    SetI,
    StrI,
    ensure_nu,
)
from nu.shapes import ReactiveSequenceRef, Shape, Slot
from nu.terms import Mode
from virtuals.collections import MutableSequenceBase

from .base import ViewRef
from .items import ItemRef


if TYPE_CHECKING:
    from nu import Interface, Nu, Sentinel
    from virtuals.loc import path


def _value_type_for(python_type: type) -> type[Interface]:
    """Map Python type to its corresponding Interface."""
    mapping: dict[type, type] = {
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
    "ListRef",
]


class ListRef[
    T,
    ItemValueT,
](
    ReactiveSequenceRef[
        T,
        ListI[T],
        ItemValueT,
    ],
    ViewRef[
        list[T],
        MutableSequenceBase,
    ],
):
    """PV sequence reference — document model + PV substrate.

    Operations work lazily on PV views without loading into memory.
    """

    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def result(self, op: Nu) -> ListI[T]:
        return ListI(op)

    def _wrap_iterable_result(self, operand: Nu) -> IteratorI:
        return IteratorI(operand)

    def _wrap_sliceable_result(self, operand: Nu) -> ListI[T]:
        return ListI(operand)  # slices stay materialized

    def _wrap_element_result(self, operand: Nu) -> AnyI:
        return AnyI(operand)

    def __init__(
        self,
        *,
        address: path.PathAddress | Nu,
        item_type: type[T],
        item_value_type: type[ItemValueT],
        view_type: type[MutableSequenceBase],
        parent: ViewRef | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        """Initialize sequence reference."""
        super().__init__(
            address=address, view_type=view_type, parent=parent, owner_shape=owner_shape
        )
        self.item_type = item_type
        self.item_value_type = item_value_type

    def _create_item_ref(
        self, index: int | Sentinel | Nu[int | Sentinel]
    ) -> ItemRef[T, ItemValueT]:
        """Create a reference to an item at the given index."""
        return ItemRef(
            address=ensure_nu(index),
            value_type=self.item_type,
            value_value_type=self.item_value_type,
            parent=self,
            owner_shape=self._owner_shape,
        )

    @classmethod
    def slot[E](
        cls,
        item_type: type[E],
        view_type: type[MutableSequenceBase] | None = None,
    ) -> ListRef[E, Value]:
        """Create a slot for this list ref type.

        Args:
            item_type: Python type of items (primitives)
            view_type: View class implementing MutableSequenceBase protocol

        Returns:
            Slot configured to create ListRef instances
        """
        from virtuals.views import ListView

        return Slot(
            cls,
            item_type=item_type,
            item_value_type=_value_type_for(item_type),
            view_type=view_type or ListView,
        )  # type: ignore
