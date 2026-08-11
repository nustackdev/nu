"""Virtuals kh57 shapes reference: sparse int-keyed map of homogeneous shapes.

Thin extension of :class:`ShapesDictRef` that pins keys to non-negative 57-bit
ints and defaults the view to :class:`~virtuals.views.Kh57View`, plus adds
``.sample(n, begin, end)`` and ``.range(begin, end)`` on top. Values are
Shapes: key descent (``ref[k]``) returns a substrate-backed :class:`ShapeRef`
at the int key, so callers can descend into per-point sub-fields
(``series.points[ts].value``, etc.).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Generic, TypeVar

from nu.domains.shape import Slot
from nu.forms import Any
from nu.lang.typeinfo import value_type_for

from .dictshape import ShapesDictRef


if TYPE_CHECKING:
    from nu.domains.shape.dsl import Shape
    from nu.lang import Nu
    from virtuals.views import Kh57ViewBase

    from .base import ViewRef


__all__ = [
    "Kh57ShapesRef",
]


T = TypeVar("T", bound="Shape")
S = TypeVar("S", bound="Shape")


class Kh57ShapesRef(ShapesDictRef[int, T], Generic[T]):
    """Sparse int-keyed mapping of homogeneous shapes with kh57 sampling.

    Inherits shape-descent semantics from :class:`ShapesDictRef`. Keys are
    always non-negative 57-bit ints; the default view is :class:`Kh57View`.
    Adds :meth:`sample` and :meth:`range` on top.
    """

    def __init__(
        self,
        address: str | int | Nu,
        *,
        shape_type: type[T],
        view_type: type[Kh57ViewBase] | None = None,
        parent_ref: ViewRef | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        from virtuals.views import Kh57View

        super().__init__(
            address,
            shape_type=shape_type,
            key_type=int,
            key_value_type=value_type_for(int),
            view_type=view_type or Kh57View,
            parent_ref=parent_ref,
            owner_shape=owner_shape,
        )

    @classmethod
    def slot(  # type: ignore[override]
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
    ) -> Any:
        """Range reservoir sample - return up to ``n`` (key, shape) pairs.

        Yields a list of ``(int_key, shape_view)`` tuples from the sub-range
        ``[begin, end)``. Deterministic given a seeded backend salt; stable
        under appends outside the queried range.
        """
        from nu.kv.interactions.kh57 import Kh57Sample

        return Any(Kh57Sample(self, n, begin, end))

    def range(
        self,
        begin: int | Nu,
        end: int | Nu,
    ) -> Any:
        """List of ``(int_key, shape_view)`` pairs in ``[begin, end)``, key-ordered."""
        from nu.kv.interactions.kh57 import Kh57Range

        return Any(Kh57Range(self, begin, end))
