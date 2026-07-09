"""Virtuals kh57 shapes reference — sparse int-keyed map of homogeneous shapes.

Wraps a virtuals :class:`~virtuals.views.Kh57View` (like :class:`Kh57Ref`) but
values are Shapes, not primitives -- the kh57 analogue of
:class:`~nu.virtuals.refs.dictshape.ShapesDictRef`. Key descent (``ref[k]``)
returns a substrate-backed :class:`ShapeRef` at the int key, so a caller can
descend into per-point sub-fields (``series.points[ts].value``, etc.).

Semantically a mutable ``Mapping[int, T]`` where ``T`` is a :class:`Shape`;
adds ``.sample(n, begin, end)`` and ``.range(begin, end)`` on top -- the same
kh57 range reservoir sampling and ordered range slice as :class:`Kh57Ref`,
just returning shape-child pairs.
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
from nu.domains.shape import ReactiveShapesMappingRef, Slot
from nu.lang.typeinfo import value_type_for

from .base import ViewRef
from .shape import ShapeRef


if TYPE_CHECKING:
    from nu import Nu
    from nu.domains.shape.dsl import Shape
    from virtuals.views import Kh57ViewBase


__all__ = [
    "Kh57ShapesRef",
]


class Kh57ShapesRef[T: Shape](ReactiveShapesMappingRef[T], ViewRef[dict[int, dict]]):
    """Sparse int-keyed mapping of homogeneous shapes with kh57 sampling."""

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

    def _wrap_result(self, op: Nu) -> DictForm[int, T]:
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

    def _wrap_mapping_result(self, operand: Nu) -> DictForm[int, T]:
        return DictForm(operand)

    def __init__(
        self,
        address: str | int | Nu,
        *,
        shape_type: type[T],
        view_type: type[Kh57ViewBase],
        parent_ref: ViewRef | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(
            address,
            item_shape_type=shape_type,
            parent_ref=parent_ref,
            owner_shape=owner_shape,
        )
        self._payload["segment"] = address
        self._payload["type_marker"] = view_type
        self._payload["value_type"] = dict
        # kh57 keys are always non-negative 57-bit ints.
        self._payload["key_type"] = int
        self._payload["key_value_type"] = value_type_for(int)

    @classmethod
    def slot[S: Shape](
        cls,
        shape_type: type[S],
        view_type: type[Kh57ViewBase] | None = None,
    ) -> Kh57ShapesRef[S]:
        """Declare a kh57 mapping slot whose values are ``shape_type`` shapes (int keys)."""
        from virtuals.views import Kh57View

        return Slot(
            cls,
            shape_type=shape_type,
            view_type=view_type or Kh57View,
        )  # type: ignore[return-value]

    @classmethod
    def _slot_kwargs_from_type_args(cls, args: tuple) -> dict[str, object]:
        """Derive slot kwargs from an annotation like ``Kh57ShapesRef[S]`` (int keys)."""
        from virtuals.views import Kh57View

        (shape_type,) = args
        return {
            "shape_type": shape_type,
            "view_type": Kh57View,
        }

    def sample(
        self,
        n: int | Nu,
        begin: int | Nu | None = None,
        end: int | Nu | None = None,
    ) -> AnyForm:
        """Range reservoir sample - return up to ``n`` (key, shape) pairs.

        Yields a list of ``(int_key, shape_view)`` tuples from the sub-range
        ``[begin, end)``. Deterministic given a seeded backend salt; stable
        under appends outside the queried range.
        """
        from nu.virtuals.interactions.kh57 import Kh57SampleQuery

        return AnyForm(Kh57SampleQuery(self, n, begin, end))

    def range(
        self,
        begin: int | Nu,
        end: int | Nu,
    ) -> AnyForm:
        """List of ``(int_key, shape_view)`` pairs in ``[begin, end)``, key-ordered."""
        from nu.virtuals.interactions.kh57 import Kh57RangeQuery

        return AnyForm(Kh57RangeQuery(self, begin, end))
