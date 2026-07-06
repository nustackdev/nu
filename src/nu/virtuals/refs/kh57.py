"""Virtuals kh57 mapping reference — sparse int-keyed map with range sampling.

Wraps a virtuals Kh57View: physical storage under kh57-encoded child segments
so range reservoir sampling (`kh57.sample`) runs with low read amplification.
Semantically a mutable mapping[int, V]; adds `.sample(n, begin, end)` and
`.range(begin, end)` on top.
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
from nu.domains.shape import ReactiveMappingRef, Slot
from nu.lang.typeinfo import value_type_for

from .base import ViewRef


if TYPE_CHECKING:
    from nu import Nu
    from nu.domains.shape.dsl import Shape
    from virtuals.views import Kh57ViewBase


__all__ = [
    "Kh57Ref",
]


class Kh57Ref[V](ReactiveMappingRef, ViewRef[dict[int, V]]):
    """Virtuals kh57 mapping reference — sparse int-keyed map with sampling.

    Keys must be non-negative 57-bit ints. Adds `.sample(n, begin, end)` and
    `.range(begin, end)` beyond the standard mapping surface.
    """

    def _wrap_result(self, op: Nu) -> DictForm[int, V]:
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

    def _wrap_mapping_result(self, operand: Nu) -> DictForm[int, V]:
        return DictForm(operand)

    def __init__(
        self,
        address: str | int | Nu,
        *,
        value_type: type[V],
        value_value_type: type,
        view_type: type[Kh57ViewBase],
        parent_ref: ViewRef | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(
            address, view_type=view_type, parent_ref=parent_ref, owner_shape=owner_shape
        )
        self._payload["value_type"] = value_type
        self._payload["value_value_type"] = value_value_type
        # kh57 keys are always non-negative 57-bit ints.
        self._payload["key_type"] = int
        self._payload["key_value_type"] = value_type_for(int)

    @classmethod
    def slot[DV](
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
    ) -> AnyForm:
        """Range reservoir sample - return up to ``n`` (key, value) pairs.

        Yields a list of ``(int_key, value)`` tuples from the sub-range
        ``[begin, end)``. Deterministic given a seeded backend salt;
        stable under appends outside the queried range.
        """
        from nu.virtuals.interactions.kh57 import Kh57SampleQuery

        return AnyForm(Kh57SampleQuery(self, n, begin, end))

    def range(
        self,
        begin: int | Nu,
        end: int | Nu,
    ) -> AnyForm:
        """List of ``(int_key, value)`` pairs in ``[begin, end)``, key-ordered."""
        from nu.virtuals.interactions.kh57 import Kh57RangeQuery

        return AnyForm(Kh57RangeQuery(self, begin, end))
