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
    from nu.lang import IntArg, StrArg
    from virtuals.views import Kh57ViewBase

    from .base import ViewRef


__all__ = [
    "Kh57ShapesRef",
]


T = TypeVar("T", bound="Shape")
S = TypeVar("S", bound="Shape")


class Kh57ShapesRef(ShapesDictRef[int, T], Generic[T]):
    """A sparse int-keyed mapping of one shape type, laid out for range sampling.

    The shape-keyed sibling of the kh57 map: keys are non-negative 57-bit
    ints, values are rows with fields of their own, and subscripting descends
    into a row rather than yielding a value. What a time series of structured
    points is stored in.

    Notes:
        - Rows are stored decomposed, so ``series[ts].value`` reads one
          field without pulling the rest of the row.
        - A key vivifies on write, as on any shape mapping.
        - Iteration and ``keys`` come back in ascending key order.
        - ``sample`` and ``range`` yield the row's view per entry, not a
          shape ref, so they are for reading a window rather than for
          descending further.

    Example:
        class Point(Shape):
            value = FloatRef.slot()
        class Series(Shape):
            points = Kh57ShapesRef.slot(Point)
        run(Series.points[1_700_000].value.set(1.5), ctx)
        run(Series.points.range(1_700_000, 1_700_100), ctx)
    """

    def __init__(
        self,
        address: StrArg | IntArg,
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
        n: IntArg,
        begin: IntArg | None = None,
        end: IntArg | None = None,
    ) -> Any:
        """Draw a uniform sample of up to ``n`` rows from a key range.

        Args:
            n: the ceiling on how many pairs come back. A range holding
                fewer than ``n`` rows yields all of them.
            begin: inclusive lower bound on the key. None leaves the range
                open at the bottom.
            end: exclusive upper bound on the key. None leaves the range
                open at the top.

        Notes:
            - Cost tracks ``n``, not the size of the range.
            - Each argument is a child, so any of them may be an expression
              or a ref read at run time.
            - Draws from the unseeded module random source. Build the
              Kh57Sample atom directly with its ``rng`` argument when a run
              has to be reproducible.
            - Stable under appends outside the queried range.

        Yields:
            A list of ``(int_key, row_view)`` pairs, unordered, each row a
            view over its stored fields. EMPTY when the container is not
            reachable.

        Example:
            run(Series.points.sample(100, begin=0, end=10_000), ctx)
        """
        from nu.kv.interactions.kh57 import Kh57Sample

        return Any(Kh57Sample(self, n, begin, end))

    def range(
        self,
        begin: IntArg,
        end: IntArg,
    ) -> Any:
        """Read a key range of rows whole, in ascending key order.

        Args:
            begin: inclusive lower bound on the key. Must be non-negative.
            end: exclusive upper bound on the key. Must stay inside the key
                space the container's layout covers.

        Notes:
            - Cost tracks the size of the range, so sample instead when the
              window grows without bound.
            - Both bounds are required, unlike on ``sample``, and both are
              children, so either may be computed at run time.
            - An empty or inverted range yields an empty list rather than an
              error; bounds outside the key space raise ValueError.

        Yields:
            A list of ``(int_key, row_view)`` pairs, ascending by key. EMPTY
            when the container is not reachable.

        Example:
            run(Series.points.range(0, 100), ctx)
        """
        from nu.kv.interactions.kh57 import Kh57Range

        return Any(Kh57Range(self, begin, end))
