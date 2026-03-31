# ruff: noqa: D102
"""Dict shapes dict reference — mapping of homogeneous shapes."""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.abc import (
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
from nu.shape import MutableShapesMappingRefBase, Slot

from .base import RefBase
from .shape import ShapeRef


if TYPE_CHECKING:
    from nu import Sentinel, Term, Value
    from nu.shape import Shape


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
    "ShapesDictRef",
]


class ShapesDictRef[K, T: Shape](
    MutableShapesMappingRefBase[K, T],
    RefBase[dict[K, dict]],
):
    """Dict shapes dict reference — mapping of homogeneous shapes."""

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
        key_type: type[K],
        key_value_type: type,
        shape_type: type[T],
        **kwargs: object,
    ) -> None:
        super().__init__(**kwargs)
        self.value_type = dict
        self.key_type = key_type
        self.key_value_type = key_value_type
        self._shape_type = shape_type

    def _create_child_ref(self, key: K | Sentinel | Term[K | Sentinel]) -> ShapeRef[T]:
        return ShapeRef(
            address=ensure_term(key),
            shape_type=self._shape_type,
            parent=self,
            owner_shape=self._owner_shape,
        )

    @classmethod
    def slot[DK, S: Shape](
        cls, shape_type: type[S], key_type: type[DK] = str
    ) -> ShapesDictRef[DK, S]:  # type: ignore[assignment]
        return Slot(
            cls,
            shape_type=shape_type,
            key_type=key_type,
            key_value_type=_value_type_for(key_type),
        )  # type: ignore[return-value]
