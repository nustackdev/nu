"""Virtuals kh57 mapping reference: sparse int-keyed map with range sampling.

Thin extension of :class:`DictRef` that pins keys to non-negative 57-bit ints,
defaults the view to :class:`~virtuals.views.Kh57View`, and adds
``.sample(n, begin, end)`` and ``.range(begin, end)`` on top of the standard
mapping surface. Physical storage lives under kh57-encoded child segments so
range reservoir sampling (``kh57.sample``) runs with low read amplification.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Generic, TypeVar

from nu.domains.shape import Slot
from nu.forms import Any
from nu.lang.typeinfo import value_type_for

from .dict import DictRef


if TYPE_CHECKING:
    from nu.domains.shape.dsl import Shape
    from nu.lang import IntArg, StrArg
    from virtuals.views import Kh57ViewBase

    from .base import ViewRef


__all__ = [
    "Kh57Ref",
]


V = TypeVar("V")
DV = TypeVar("DV")


class Kh57Ref(DictRef[int, V], Generic[V]):
    """A sparse int-keyed mapping in KV storage, laid out for range sampling.

    Same mapping surface as a dict slot, with the keys pinned to non-negative
    57-bit ints and the physical layout encoded so that a sample or a scan
    over a key range reads only that range. Built for the case where the map
    holds billions of entries and the question is about a window of them.

    Notes:
        - Keys are ints; a key outside the non-negative 57-bit range is out
          of contract.
        - Iteration and ``keys`` come back in ascending key order, whatever
          order the writes happened in.
        - ``sample`` and ``range`` are what the layout buys; everything else
          behaves as it does on a plain dict slot.
        - Values are plain values here. Reach for Kh57ShapesRef when each
          entry should be a shape with fields of its own.

    Example:
        class Ledger(Shape):
            entries = Kh57Ref.slot(int)
        run(Ledger.entries.set_item(42, 100), ctx)
        run(Ledger.entries.sample(10, begin=0, end=1000), ctx)
    """

    def __init__(
        self,
        address: StrArg | IntArg,
        *,
        value_type: type[V],
        value_value_type: type,
        view_type: type[Kh57ViewBase] | None = None,
        parent_ref: ViewRef | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        from virtuals.views import Kh57View

        super().__init__(
            address,
            value_type=value_type,
            key_type=int,
            key_value_type=value_type_for(int),
            value_value_type=value_value_type,
            view_type=view_type or Kh57View,
            parent_ref=parent_ref,
            owner_shape=owner_shape,
        )

    @classmethod
    def slot(  # type: ignore[override]
        cls,
        value_type: type[DV],
        view_type: type[Kh57ViewBase] | None = None,
    ) -> Kh57Ref[DV]:
        """Declare a kh57 mapping slot with ``value_type`` values (int keys)."""
        from virtuals.views import Kh57View

        return Slot(
            cls,
            value_type=value_type,
            value_value_type=value_type_for(value_type),
            view_type=view_type or Kh57View,
        )  # type: ignore[return-value]

    @classmethod
    def _slot_kwargs_from_type_args(cls, args: tuple) -> dict[str, object]:
        """Derive slot kwargs from an annotation like ``Kh57Ref[V]`` (int keys)."""
        from virtuals.views import Kh57View

        (value_type,) = args
        return {
            "value_type": value_type,
            "value_value_type": value_type_for(value_type),
            "view_type": Kh57View,
        }

    def sample(
        self,
        n: IntArg,
        begin: IntArg | None = None,
        end: IntArg | None = None,
    ) -> Any:
        """Draw a uniform sample of up to ``n`` entries from a key range.

        Args:
            n: the ceiling on how many pairs come back. A range holding
                fewer than ``n`` entries yields all of them.
            begin: inclusive lower bound on the key. None leaves the range
                open at the bottom.
            end: exclusive upper bound on the key. None leaves the range
                open at the top.

        Notes:
            - Cost tracks ``n``, not the size of the range, so a window
              holding a billion entries samples as cheaply as a small one.
            - Each argument is a child, so any of them may be an expression
              or a ref read at run time.
            - Draws from the unseeded module random source. Build the
              Kh57Sample atom directly with its ``rng`` argument when a run
              has to be reproducible.
            - Stable under appends outside the queried range.

        Yields:
            A list of ``(int_key, value)`` pairs, unordered. EMPTY when the
            container is not reachable.

        Example:
            run(Ledger.entries.sample(100, begin=0, end=10_000), ctx)
        """
        from nu.kv.interactions.kh57 import Kh57Sample

        return Any(Kh57Sample(self, n, begin, end))

    def range(
        self,
        begin: IntArg,
        end: IntArg,
    ) -> Any:
        """Read a key range whole, in ascending key order.

        Args:
            begin: inclusive lower bound on the key. Must be non-negative.
            end: exclusive upper bound on the key. Must stay inside the key
                space the container's layout covers.

        Notes:
            - Cost tracks the size of the range, so this is the wrong call
              for a window that grows without bound; sample that instead.
            - Both bounds are required, unlike on ``sample``, and both are
              children, so either may be computed at run time.
            - An empty or inverted range yields an empty list rather than an
              error; bounds outside the key space raise ValueError.

        Yields:
            A list of ``(int_key, value)`` pairs, ascending by key. EMPTY
            when the container is not reachable.

        Example:
            run(Ledger.entries.range(0, 100), ctx)
        """
        from nu.kv.interactions.kh57 import Kh57Range

        return Any(Kh57Range(self, begin, end))
