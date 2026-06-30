"""Dict shapes dict reference — mapping of homogeneous shapes.

Key descent (``ref[k]``) is the blueprint's ``__getitem__``: it returns a
``ShapeRef`` at the key with this ref as ``parent_ref``. The value shape type is
passed to the blueprint as ``item_shape_type``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu import (
    AnyForm,
    DictForm,
    DictItemsForm,
    DictKeysForm,
    DictValuesForm,
    IteratorForm,
)
from nu.domains.shape import MutableShapesMappingRef, Slot

from ._typemap import value_type_for
from .base import RefBase
from .shape import ShapeRef


if TYPE_CHECKING:
    from nu import Nu
    from nu.domains.shape.dsl import Shape


__all__ = [
    "ShapesDictRef",
]


class ShapesDictRef[K, T: Shape](MutableShapesMappingRef, RefBase[dict[K, dict]]):
    """Dict shapes dict reference — mapping of homogeneous shapes."""

    def __getitem__(self, key: object) -> ShapeRef:
        """Navigate to the shape at ``key`` as a substrate-backed mem ShapeRef."""
        return ShapeRef(
            key,
            shape_type=self._item_shape_type,
            parent_ref=self,
            owner_shape=self._owner_shape,
        )

    def result(self, op: Nu) -> DictForm:
        """Wrap a mapping-level op result as a DictForm."""
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
        address: str | int | Nu,
        *,
        shape_type: type[T],
        key_type: type[K],
        key_value_type: type,
        parent_ref: RefBase | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(
            address,
            item_shape_type=shape_type,
            parent_ref=parent_ref,
            owner_shape=owner_shape,
        )
        self.value_type: type = dict
        self.key_type = key_type
        self.key_value_type = key_value_type

    @classmethod
    def slot[DK, S: Shape](
        cls, shape_type: type[S], key_type: type[DK] = str
    ) -> ShapesDictRef[DK, S]:  # type: ignore[assignment]
        """Declare a mapping slot whose values are ``shape_type`` shapes."""
        return Slot(
            cls,
            shape_type=shape_type,
            key_type=key_type,
            key_value_type=value_type_for(key_type),
        )  # type: ignore[return-value]
