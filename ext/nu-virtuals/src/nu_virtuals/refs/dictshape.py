# ruff: noqa: D102
"""PV shapes dict reference — document model + PV substrate."""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu import (
    AnyI,
    BoolI,
    BytesI,
    DictI,
    DictItemsI,
    DictKeysI,
    DictValuesI,
    FloatI,
    IntI,
    IteratorI,
    ListI,
    SetI,
    StrI,
    ensure_nu,
)
from nu.shapes import ReactiveShapesMappingRef, Shape, Slot
from virtuals.collections import MutableMappingBase

from .base import ViewRef
from .shape import ShapeRef


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
    "ShapesDictRef",
]


class ShapesDictRef[
    K: int | str,
    T: Shape,
    KeyValueT,
](
    ReactiveShapesMappingRef[
        K,
        T,
    ],
    ViewRef[
        dict[K, dict],
        MutableMappingBase,
    ],
):
    """PV shapes dict reference — document model + PV substrate."""

    def result(self, op: Nu) -> DictI:
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
        address: path.PathAddress | Nu,
        key_type: type[K],
        key_value_type: type[KeyValueT],
        shape_type: type[T],
        view_type: type[MutableMappingBase],
        parent: ViewRef | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        """Initialize mapping shape reference."""
        super().__init__(
            address=address, view_type=view_type, parent=parent, owner_shape=owner_shape
        )
        self.value_type = dict
        self.key_type = key_type
        self.key_value_type = key_value_type
        self._shape_type = shape_type

    def _create_child_ref(self, key: K | Sentinel | Nu[K | Sentinel]) -> ShapeRef[T]:
        """Create a reference to a shape at the given key."""
        from virtuals.views import DictView

        return ShapeRef(
            address=ensure_nu(key),
            shape_type=self._shape_type,
            view_type=DictView,
            parent=self,
            owner_shape=self._owner_shape,
        )

    @classmethod
    def slot[DK: (int, str), S: Shape](
        cls,
        shape_type: type[S],
        view_type: type[MutableMappingBase] | None = None,
        key_type: type[DK] = str,  # type: ignore[assignment]
    ) -> ShapesDictRef[DK, S, Value]:
        """Create a slot for this shapes dict ref type.

        Args:
            shape_type: Shape class for values
            view_type: View class implementing MutableMappingBase protocol
            key_type: Python type for keys (default: str)

        Returns:
            Slot configured to create ShapesDictRef instances
        """
        from virtuals.views import DictView

        return Slot(
            cls,
            key_type=key_type,
            key_value_type=_value_type_for(key_type),
            shape_type=shape_type,
            view_type=view_type or DictView,
        )  # type: ignore
