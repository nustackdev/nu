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
    from nu.lang import Nu
    from virtuals.views import Kh57ViewBase

    from .base import ViewRef


__all__ = [
    "Kh57Ref",
]


V = TypeVar("V")
DV = TypeVar("DV")


class Kh57Ref(DictRef[int, V], Generic[V]):
    """Sparse int-keyed mapping with kh57-encoded layout for range sampling.

    Inherits all mapping semantics from :class:`DictRef`. Keys are always
    non-negative 57-bit ints; the default view is :class:`Kh57View`. Adds
    :meth:`sample` and :meth:`range` on top.
    """

    def __init__(
        self,
        address: str | int | Nu,
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
        n: int | Nu,
        begin: int | Nu | None = None,
        end: int | Nu | None = None,
    ) -> Any:
        """Range reservoir sample - return up to ``n`` (key, value) pairs.

        Yields a list of ``(int_key, value)`` tuples from the sub-range
        ``[begin, end)``. Deterministic given a seeded backend salt;
        stable under appends outside the queried range.
        """
        from nu.kv.interactions.kh57 import Kh57Sample

        return Any(Kh57Sample(self, n, begin, end))

    def range(
        self,
        begin: int | Nu,
        end: int | Nu,
    ) -> Any:
        """List of ``(int_key, value)`` pairs in ``[begin, end)``, key-ordered."""
        from nu.kv.interactions.kh57 import Kh57Range

        return Any(Kh57Range(self, begin, end))
