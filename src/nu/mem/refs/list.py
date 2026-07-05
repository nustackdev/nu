"""Dict sequence reference — ordered container backed by nested list."""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu import AnyForm, IteratorForm, ListForm
from nu.domains.shape import MutableSequenceRef, Slot

from ._typemap import value_type_for
from .base import RefBase
from .items import ItemRef


if TYPE_CHECKING:
    from nu import Nu
    from nu.domains.shape.dsl import Shape


__all__ = [
    "ListRef",
]


class ListRef[T](MutableSequenceRef["ItemRef"], RefBase[list[T]]):
    """Dict sequence reference — ordered container backed by nested list."""

    def _wrap_item_ref(self, address: object) -> ItemRef:
        """Navigate to the element at ``address`` as a substrate-backed mem ItemRef."""
        return ItemRef(
            address,
            value_type=self._payload["item_type"],
            value_value_type=self._payload["item_value_type"],
            parent_ref=self,
            owner_shape=self._owner_shape,
        )

    def _wrap_result(self, op: Nu) -> ListForm[T]:
        """Wrap a sequence-level op result as a ListForm."""
        return ListForm(op)

    def _wrap_iterable_result(self, operand: Nu) -> IteratorForm:
        return IteratorForm(operand)

    def _wrap_sliceable_result(self, operand: Nu) -> ListForm[T]:
        return ListForm(operand)  # slices stay materialized

    def _wrap_element_result(self, operand: Nu) -> AnyForm:
        return AnyForm(operand)

    def __init__(
        self,
        address: str | int | Nu,
        *,
        item_type: type[T],
        item_value_type: type,
        parent_ref: RefBase | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(address, parent_ref=parent_ref, owner_shape=owner_shape)
        self._payload["item_type"] = item_type
        self._payload["item_value_type"] = item_value_type

    @classmethod
    def slot[E](cls, item_type: type[E]) -> ListRef[E]:
        """Declare a list slot holding elements of ``item_type``."""
        return Slot(
            cls,
            item_type=item_type,
            item_value_type=value_type_for(item_type),
        )  # type: ignore[return-value]
