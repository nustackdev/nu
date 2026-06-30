# ruff: noqa: D102
"""Dict sequence reference — ordered container backed by nested list."""

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
from nu.shapes import MutableSequenceRef, Slot
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
    "ListRef",
]


class ListRef[T](
    MutableSequenceRef[T, ListForm[T], AnyForm],
    RefBase[list[T]],
):
    """Dict sequence reference — ordered container backed by nested list."""

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
        item_type: type[T],
        item_value_type: type,
        **kwargs: object,
    ) -> None:
        super().__init__(**kwargs)
        self.item_type = item_type
        self.item_value_type = item_value_type

    def _create_item_ref(self, index: int | Sentinel | Nu[int | Sentinel]) -> ItemRef[T, ...]:
        return ItemRef(
            address=index,
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
