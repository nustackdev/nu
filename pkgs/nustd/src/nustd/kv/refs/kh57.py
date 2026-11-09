"""kv sampled map: an int-keyed mapping laid out so a key range samples cheaply.

A mapping slot whose keys are pinned to non-negative 57-bit ints and whose
storage is kh57-encoded, so sampling or scanning a window of keys reads only
that window. Its order is the hashed layout's, not insertion order, so it is a
plain ``Mapping`` (no ``reversed``, no paging, no dict-only calls), not a
``DictRef``; descent and typing are a ``DictRef``'s.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Generic, TypeVar

from nu.domains.shape import ReactiveMappingRef, Slot
from nu.forms import Object
from nu.lang.typeinfo import TypeInfo
from virtuals.views import Kh57View, Kh57ViewBase

from .base import ViewRef, _refuse_container_value
from .containers import _MappingDescent, _require_view


if TYPE_CHECKING:
    from nu.lang import IntArg


__all__ = [
    "Kh57Ref",
]


V = TypeVar("V")
DV = TypeVar("DV")


class Kh57Ref(_MappingDescent[int, V], ReactiveMappingRef, ViewRef[dict[int, V]], Generic[V]):
    """A sparse int-keyed mapping in KV storage, laid out for range sampling.

    The Python ``MutableMapping`` surface, with the keys pinned to non-negative
    57-bit ints and the physical layout encoded so that a sample or a scan
    over a key range reads only that range. Built for the case where the map
    holds billions of entries and the question is about a window of them.

    Notes:
        - Keys are ints; a key outside the non-negative 57-bit range is out
          of contract.
        - Iteration and ``keys`` come back in ascending key order, whatever
          order the writes happened in.
        - ``sample`` and ``range`` are what the layout buys. The rest is a
          ``MutableMapping``: no ``reversed`` reads or paging, and none of
          the dict-only calls (``copy``, ``merge``); ``extract()`` first.
        - Declare a Shape as the value and each entry is a row with fields
          of its own: ``series[ts].value`` reads one field of one row.
          ``sample`` and ``range`` then yield each row as a view over its
          stored fields, for reading a window rather than descending.

    Example:
        class Ledger(Shape):
            entries = Kh57Ref.slot(int)
        run(Ledger.entries.set_item(42, 100), ctx)
        run(Ledger.entries.sample(10, begin=0, end=1000), ctx)
    """

    _default_view = Kh57View

    @classmethod
    def slot(cls, value: type[DV], *, view: type[Kh57ViewBase] | None = None) -> Kh57Ref[DV]:
        """Declare a kh57 mapping slot holding ``value`` under int keys.

        Args:
            value: what each key holds: a Python type, a Shape, or a kv leaf
                class.
            view: the View class laying the map out. Defaults to
                ``Kh57View``.

        Notes:
            - ``points: Kh57Ref[Point]`` as an annotation declares the same
              slot.
        """
        _refuse_container_value(cls, value)
        _require_view(cls, view, (Kh57ViewBase,), "a kh57 view, as Kh57View")
        declared = TypeInfo.from_annotation(cls[value])  # type: ignore[index]
        return Slot(cls, type_info=declared, view_type=view)  # type: ignore[return-value]

    def sample(
        self,
        n: IntArg,
        begin: IntArg | None = None,
        end: IntArg | None = None,
    ) -> Object:
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
            A list of ``(int_key, value)`` pairs, unordered.

        Example:
            run(Ledger.entries.sample(100, begin=0, end=10_000), ctx)
        """
        from nustd.kv.interactions.kh57 import Kh57Sample

        return Object(Kh57Sample(self, n, begin, end))

    def range(
        self,
        begin: IntArg,
        end: IntArg,
    ) -> Object:
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
            A list of ``(int_key, value)`` pairs, ascending by key.

        Example:
            run(Ledger.entries.range(0, 100), ctx)
        """
        from nustd.kv.interactions.kh57 import Kh57Range

        return Object(Kh57Range(self, begin, end))
