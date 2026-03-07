# ruff: noqa: D102
"""PV shapes dict reference — document model + PV substrate."""

from __future__ import annotations

from typing import TYPE_CHECKING, Self

from virtuals.collections import MutableMappingView

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
from everybase.shape import ReactiveShapesMappingRefBase, Shape, Slot

from .base import ViewRef
from .shape import ShapeRef


if TYPE_CHECKING:
    from virtuals.loc import path

    from everybase import Sentinel, Term, Value


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
    "ShapesDictRef",
]


class ShapesDictRef[
    K: int | str,
    T: Shape,
    KeyValueT,
](
    ReactiveShapesMappingRefBase[
        K,
        T,
    ],
    ViewRef[
        dict[K, dict],
        MutableMappingView,
    ],
):
    """PV shapes dict reference — document model + PV substrate."""

    def result(self, op: Term) -> DictValue:
        return DictValue(op)

    def _wrap_keys_result(self, operand: Term) -> ListValue:
        return ListValue(operand)

    def _wrap_values_result(self, operand: Term) -> ListValue:
        return ListValue(operand)

    def _wrap_items_result(self, operand: Term) -> ListValue:
        return ListValue(operand)

    def _wrap_iterable_result(self, operand: Term) -> ListValue:
        return ListValue(operand)

    def _wrap_value_result(self, operand: Term) -> AnyValue:
        return AnyValue(operand)

    def _wrap_element_result(self, operand: Term) -> AnyValue:
        return AnyValue(operand)

    def __init__(
        self,
        *,
        address: path.PathAddress | Term,
        key_type: type[K],
        key_value_type: type[KeyValueT],
        shape_type: type[T],
        view_type: type[MutableMappingView],
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

    def _create_child_ref(self, key: K | Sentinel | Term[K | Sentinel]) -> ShapeRef[T]:
        """Create a reference to a shape at the given key."""
        from eb_pv.views import DictView

        return ShapeRef(
            address=ensure_term(key),
            shape_type=self._shape_type,
            view_type=DictView,
            parent=self,
            owner_shape=self._owner_shape,
        )

    @classmethod
    def slot(
        cls,
        shape_type: type[T],
        view_type: type[MutableMappingView] | None = None,
        key_type: type[K] = str,
    ) -> Self:
        """Create a slot for this shapes dict ref type.

        Args:
            shape_type: Shape class for values
            view_type: View class implementing MutableMappingView protocol
            key_type: Python type for keys (default: str)

        Returns:
            Slot configured to create ShapesDictRef instances
        """
        from eb_pv.views import DictView

        return Slot(
            cls,
            key_type=key_type,
            key_value_type=_value_type_for(key_type),
            shape_type=shape_type,
            view_type=view_type or DictView,
        )  # type: ignore
