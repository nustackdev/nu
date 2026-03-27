# ruff: noqa: D102
"""PV shapes dict reference — document model + PV substrate."""

from __future__ import annotations

from typing import TYPE_CHECKING

from virtuals.collections import MutableMappingBase

from everybase.abc import (
    AnyValue,
    BoolValue,
    BytesValue,
    DictItemsValue,
    DictKeysValue,
    DictValue,
    DictValuesValue,
    FloatValue,
    IntValue,
    IteratorValue,
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
        MutableMappingBase,
    ],
):
    """PV shapes dict reference — document model + PV substrate."""

    def result(self, op: Term) -> DictValue:
        return DictValue(op)

    def _wrap_keys_result(self, operand: Term) -> DictKeysValue:
        return DictKeysValue(operand)

    def _wrap_values_result(self, operand: Term) -> DictValuesValue:
        return DictValuesValue(operand)

    def _wrap_items_result(self, operand: Term) -> DictItemsValue:
        return DictItemsValue(operand)

    def _wrap_iterable_result(self, operand: Term) -> IteratorValue:
        return IteratorValue(operand)

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
        view_type: type[MutableMappingBase],
        parent: ViewRef | None = None,
        owner_shape: type[Shape] | None = None,
        primitive: bool = False,
    ) -> None:
        """Initialize mapping shape reference."""
        super().__init__(
            address=address, view_type=view_type, parent=parent, owner_shape=owner_shape
        )
        self.value_type = dict
        self.key_type = key_type
        self.key_value_type = key_value_type
        self._shape_type = shape_type
        self.primitive = primitive

    def _create_child_ref(self, key: K | Sentinel | Term[K | Sentinel]) -> ShapeRef[T]:
        """Create a reference to a shape at the given key."""
        from virtuals.views import DictView

        return ShapeRef(
            address=ensure_term(key),
            shape_type=self._shape_type,
            view_type=DictView,
            parent=self,
            owner_shape=self._owner_shape,
        )

    def store(self, value: object) -> object:
        """Store collection. If primitive=True, stores as single blob."""
        if self.primitive:
            from eb_virtuals.morphisms.collection import CollectionPrimitiveStoreCmd
            from everybase.abc import NoneValue, ensure_term

            return NoneValue(CollectionPrimitiveStoreCmd(self, ensure_term(value)))
        return super().store(value)

    @classmethod
    def slot[DK: (int, str), S: Shape](
        cls,
        shape_type: type[S],
        view_type: type[MutableMappingBase] | None = None,
        key_type: type[DK] = str,  # type: ignore[assignment]
        *,
        primitive: bool = False,
    ) -> ShapesDictRef[DK, S, Value]:
        """Create a slot for this shapes dict ref type.

        Args:
            shape_type: Shape class for values
            view_type: View class implementing MutableMappingBase protocol
            key_type: Python type for keys (default: str)
            primitive: If True, store entire collection as single blob

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
            primitive=primitive,
        )  # type: ignore
