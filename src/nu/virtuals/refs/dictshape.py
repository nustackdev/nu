"""Virtuals shapes dict reference: mapping of homogeneous shapes.

Key descent (``ref[k]``) is overridden to return a substrate-backed virtuals
``ShapeRef`` at the key, with this ref as ``parent_ref``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.domains.shape import ReactiveShapesMappingRef, Slot
from nu.forms import Any, Dict, DictItems, DictKeys, DictValues, Iterator
from nu.lang.typeinfo import value_type_for

from .base import ViewRef
from .shape import ShapeRef


if TYPE_CHECKING:
    from nu.domains.shape.dsl import Shape
    from nu.lang import Nu
    from virtuals.collections import MutableMappingBase


__all__ = [
    "ShapesDictRef",
]


class ShapesDictRef[K, T: Shape](ReactiveShapesMappingRef[T], ViewRef[dict[K, dict]]):
    """Virtuals shapes dict reference: mapping of homogeneous shapes."""

    def _wrap_item_ref(self, address: object) -> ShapeRef:
        """Navigate to the shape at ``address`` as a substrate-backed virtuals ShapeRef."""
        from virtuals.views import DictView

        return ShapeRef(
            address,
            shape_type=self._payload["item_shape_type"],
            view_type=DictView,
            parent_ref=self,
            owner_shape=self._owner_shape,
        )

    def _wrap_result(self, op: Nu) -> Dict:
        """Wrap a mapping-level op result as a Dict."""
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
        key_type: type[K],
        key_value_type: type,
        view_type: type[MutableMappingBase] | None = None,
        parent_ref: ViewRef | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        if view_type is None:
            from virtuals.views import DictView

            view_type = DictView
        super().__init__(
            address,
            item_shape_type=shape_type,
            parent_ref=parent_ref,
            owner_shape=owner_shape,
        )
        self._payload["segment"] = address
        self._payload["type_marker"] = view_type
        self._payload["value_type"] = dict
        self._payload["key_type"] = key_type
        self._payload["key_value_type"] = key_value_type

    @classmethod
    def slot[DK, S: Shape](
        cls,
        shape_type: type[S],
        view_type: type[MutableMappingBase] | None = None,
        key_type: type[DK] = str,  # type: ignore[assignment]
    ) -> ShapesDictRef[DK, S]:
        """Declare a mapping slot whose values are ``shape_type`` shapes."""
        from virtuals.views import DictView

        return Slot(
            cls,
            shape_type=shape_type,
            key_type=key_type,
            key_value_type=value_type_for(key_type),
            view_type=view_type or DictView,
        )  # type: ignore[return-value]

    @classmethod
    def _slot_kwargs_from_type_args(cls, args: tuple) -> dict[str, object]:
        """Derive slot kwargs from an annotation like ``ShapesDictRef[K, S]``."""
        from virtuals.views import DictView

        key_type, shape_type = args
        return {
            "shape_type": shape_type,
            "key_type": key_type,
            "key_value_type": value_type_for(key_type),
            "view_type": DictView,
        }
