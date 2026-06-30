"""Dict shape reference — structured container backed by nested dict.

Field descent (``ShapeRef.field``) is the blueprint's ``__getattr__``: it
resolves the slot to the field's own mem ref (``StrRef``, ``IntRef``, ...) with
this ref as ``parent_ref``, so navigation rides the substrate automatically.
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
from nu.domains.shape import MutableShapeRef, Slot

from .base import RefBase


if TYPE_CHECKING:
    from nu import Nu
    from nu.domains.shape.dsl import Shape


__all__ = [
    "ShapeRef",
]


class ShapeRef[T: Shape](MutableShapeRef, RefBase[dict[str, object]]):
    """Dict shape reference — structured container backed by nested dict."""

    def result(self, op: Nu) -> DictForm[str, object]:
        """Wrap a shape-level op result as a DictForm."""
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
        parent_ref: RefBase | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(
            address,
            shape_type=shape_type,
            parent_ref=parent_ref,
            owner_shape=owner_shape,
        )
        self.key_type: type = str
        self.value_type: type = object

    @classmethod
    def slot[S: Shape](cls, shape_type: type[S]) -> ShapeRef[S]:
        """Declare a slot holding a nested ``shape_type`` shape."""
        return Slot(cls, shape_type=shape_type)  # type: ignore[return-value]
