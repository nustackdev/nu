# ruff: noqa: D102
"""virtuals sequence reference — document model + virtuals substrate."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from nu import (
    AnyForm,
    BoolForm,
    BytesForm,
    DictForm,
    FloatForm,
    IntForm,
    IteratorForm,
    ListForm,
    SetForm,
    StrForm,
)
from nu.shapes import ReactiveSequenceRef, Shape, Slot
from nu.terms import Mode
from virtuals.collections import MutableSequenceBase

from .base import ViewRef
from .items import ItemRef


if TYPE_CHECKING:
    from nu import Form, Nu, Sentinel
    from virtuals.loc import path


def _value_type_for(python_type: type) -> type[Form]:
    """Map Python type to its corresponding Form."""
    mapping: dict[type, type] = {
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
    "ListRef",
]


class ListRef[
    T,
    ItemValueT,
](
    ReactiveSequenceRef[
        T,
        ListForm[T],
        ItemValueT,
    ],
    ViewRef[
        list[T],
        MutableSequenceBase,
    ],
):
    """virtuals sequence reference — document model + virtuals substrate.

    Operations work lazily on virtuals views without loading into memory.
    """

    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})

    def result(self, op: Nu) -> ListForm[T]:
        return ListForm(op)

    def _wrap_iterable_result(self, operand: Nu) -> IteratorForm:
        return IteratorForm(operand)

    def _wrap_sliceable_result(self, operand: Nu) -> ListForm[T]:
        return ListForm(operand)  # slices stay materialized

    def _wrap_element_result(self, operand: Nu) -> AnyForm:
        return AnyForm(operand)

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
            address=index,
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
