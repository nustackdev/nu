"""Virtuals shape reference — structured container backed by a virtuals View.

Field descent (``ref.field`` / ``ref["field"]``) is the blueprint's
``__getattr__`` / ``__getitem__``: it resolves the slot to the field's own
virtuals ref (``StrRef``, ``IntRef``, ...) with this ref as ``parent_ref``, so
navigation rides the substrate automatically.
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

from .base import Facet, ViewRef


if TYPE_CHECKING:
    from nu import Nu
    from nu.domains.shape.dsl import Shape
    from virtuals.collections import MutableMappingBase


__all__ = [
    "ShapeRef",
]


class ShapeRef[T: Shape](MutableShapeRef, ViewRef[dict[str, object]]):
    """Virtuals shape reference — structured container backed by a virtuals View."""

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
        view_type: type[MutableMappingBase] | None = None,
        parent_ref: ViewRef | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        # MutableShapeRef.__init__ wires the _StructuredRef path + shape_type;
        # the ViewRef substrate attributes are set explicitly below since the
        # shape blueprint __init__ does not thread **kwargs to ViewRef.
        if view_type is None:
            from virtuals.views import DictView

            view_type = DictView
        super().__init__(
            address,
            shape_type=shape_type,
            parent_ref=parent_ref,
            owner_shape=owner_shape,
        )
        self._segment = address
        self._view_type = view_type
        self._facet = Facet.LAZY
        self.key_type: type = str
        self.value_type: type = object

    @classmethod
    def slot[S: Shape](
        cls, shape_type: type[S], view_type: type[MutableMappingBase] | None = None
    ) -> ShapeRef[S]:
        """Declare a slot holding a nested ``shape_type`` shape."""
        from virtuals.views import DictView

        return Slot(cls, shape_type=shape_type, view_type=view_type or DictView)  # type: ignore[return-value]
