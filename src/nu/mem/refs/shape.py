"""Dict shape reference: structured container backed by nested dict.

Field descent (``ShapeRef.field``) is the blueprint's ``__getattr__``: it
resolves the slot to the field's own mem ref (``StrRef``, ``IntRef``, ...) with
this ref as ``parent_ref``, so navigation rides the substrate automatically.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Generic, TypeVar

from nu.domains.shape import MutableShapeRef, Slot
from nu.forms import Any, Dict, DictItems, DictKeys, DictValues, Iterator

from .base import RefBase


if TYPE_CHECKING:
    from nu.domains.shape.dsl import Shape
    from nu.lang import Nu


__all__ = [
    "ShapeRef",
]


T = TypeVar("T", bound="Shape")


S = TypeVar("S", bound="Shape")


class ShapeRef(MutableShapeRef, RefBase[dict[str, object]], Generic[T]):
    """Dict shape reference: structured container backed by nested dict."""

    def _wrap_result(self, op: Nu) -> Dict[str, object]:
        """Wrap a shape-level op result as a Dict."""
        return Dict(op)

    def _wrap_keys_result(self, operand: Nu) -> DictKeys:
        return DictKeys(operand)

    def _wrap_values_result(self, operand: Nu) -> DictValues:
        return DictValues(operand)

    def _wrap_items_result(self, operand: Nu) -> DictItems:
        return DictItems(operand)

    def _wrap_iterable_result(self, operand: Nu) -> Iterator:
        return Iterator(operand)

    def _wrap_value_result(self, operand: Nu) -> Any:
        return Any(operand)

    def _wrap_element_result(self, operand: Nu) -> Any:
        return Any(operand)

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
        self._payload["key_type"] = str
        self._payload["value_type"] = object

    @classmethod
    def slot(cls, shape_type: type[S]) -> S:
        """Declare a slot holding a nested ``shape_type`` shape.

        Statically returns ``S`` (the shape class) so that the annotation
        ``field: Order = ShapeRef.slot(Order)`` type-checks and dot-nav
        autocompletes over ``Order``'s slots. Runtime returns a ``Slot`` -
        replaced with a ``ShapeRef`` by ``ShapeMeta``.
        """
        return Slot(cls, shape_type=shape_type)  # type: ignore[return-value]

    @classmethod
    def _slot_kwargs_from_type_args(cls, args: tuple) -> dict[str, object]:
        """Derive slot kwargs from an annotation like ``ShapeRef[Shape]``."""
        (shape_type,) = args
        return {"shape_type": shape_type}
