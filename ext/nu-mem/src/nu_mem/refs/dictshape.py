# ruff: noqa: D102
"""Dict shapes dict reference — mapping of homogeneous shapes."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from nu import (
    AnyForm,
    BoolForm,
    BytesForm,
    DictForm,
    DictItemsForm,
    DictKeysForm,
    DictValuesForm,
    FloatForm,
    IntForm,
    IteratorForm,
    ListForm,
    SetForm,
    StrForm,
)
from nu.shapes import MutableShapesMappingRef, Slot
from nu.terms import Mode

from .base import RefBase
from .shape import ShapeRef


if TYPE_CHECKING:
    from nu import Form, Nu, Sentinel
    from nu.shapes import Shape


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
    "ShapesDictRef",
]


class ShapesDictRef[K, T: Shape](
    MutableShapesMappingRef[K, T],
    RefBase[dict[K, dict]],
):
    """Dict shapes dict reference — mapping of homogeneous shapes."""

    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})

    def result(self, op: Nu) -> DictForm:
        return DictForm(op)

    def _wrap_keys_result(self, operand: Nu) -> DictKeysForm:
        return DictKeysForm(operand)

    def _wrap_values_result(self, operand: Nu) -> DictValuesForm:
        return DictValuesForm(operand)

    def _wrap_items_result(self, operand: Nu) -> DictItemsForm:
        return DictItemsForm(operand)

    def _wrap_iterable_result(self, operand: Nu) -> IteratorForm:
        return IteratorForm(operand)

    def _wrap_value_result(self, operand: Nu) -> AnyForm:
        return AnyForm(operand)

    def _wrap_element_result(self, operand: Nu) -> AnyForm:
        return AnyForm(operand)

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

    def _create_child_ref(self, key: K | Sentinel | Nu[K | Sentinel]) -> ShapeRef[T]:
        return ShapeRef(
            address=key,
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
