# ruff: noqa: D102
"""Dict sequence reference — ordered container backed by nested list."""

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
from nu.shapes import MutableSequenceRef, Slot
from nu.terms import Mode

from .base import RefBase
from .items import ItemRef


if TYPE_CHECKING:
    from nu import Interface, Nu, Sentinel


def _value_type_for(python_type: type) -> type[Interface]:
    """Map Python type to its corresponding Interface."""
    mapping: dict[type, type[Interface]] = {
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


class ListRef[T](
    MutableSequenceRef[T, ListI[T], AnyI],
    RefBase[list[T]],
):
    """Dict sequence reference — ordered container backed by nested list."""

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
