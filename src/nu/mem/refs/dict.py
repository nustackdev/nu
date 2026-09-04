"""Dict mapping reference: key-value container backed by nested dict."""

from __future__ import annotations

from typing import TYPE_CHECKING, Generic, TypeVar

from nu.domains.shape import MutableMappingRef, Slot
from nu.forms import Any, Dict, DictItems, DictKeys, DictValues, Iterator
from nu.lang.typeinfo import value_type_for

from .base import RefBase
from .items import ItemRef


if TYPE_CHECKING:
    from nu.domains.shape.dsl import Shape
    from nu.lang import IntArg, Nu, StrArg


__all__ = [
    "DictRef",
]


K = TypeVar("K")
V = TypeVar("V")


DK = TypeVar("DK")
DV = TypeVar("DV")


class DictRef(MutableMappingRef["ItemRef"], RefBase[dict[K, V]], Generic[K, V]):
    """A mapping slot in the dict substrate, holding one plain dict of values.

    Subscripting descends rather than reads: ``ref[k]`` is an ``ItemRef`` at
    that key inside the stored dict, a ref in its own right that can be set,
    erased or read on its own. The mapping calls (``keys``, ``items``,
    ``update``, ...) act on the dict as a whole.

    Args:
        address: this level's key, a literal or a Nu term yielding one.

    Notes:
        - The stored value is an ordinary dict and a read hands back that
          live object, so a mutation through the ref is visible to anyone
          else holding it.
        - In-place calls read the container first and do nothing when the
          slot is absent, so ``set`` an empty dict before the first
          ``set_item``.
        - The declared key and value types are metadata; nothing coerces or
          rejects what is written.

    Yields:
        The stored dict. EMPTY when the slot was never written.

    Example:
        >>> class Port(nu.Shape):
        ...     meta = nu.mem.DictRef.slot(int)
        >>> data = {"meta": {"a": 1}}
        >>> ctx = nu.Context().bind(dict, data, Port)
        >>> _ = nu.run(Port.meta.set_item("b", 2), ctx)
        >>> nu.run(Port.meta["b"], ctx)[0]
        2
        >>> nu.run(Port.meta.len(), ctx)[0]
        2
    """

    def _wrap_item_ref(self, address: object) -> ItemRef:
        """Navigate to the value at ``address`` as a substrate-backed mem ItemRef."""
        return ItemRef(
            address,
            value_type=self._payload["value_type"],
            value_value_type=self._payload["value_value_type"],
            parent_ref=self,
            owner_shape=self._owner_shape,
        )

    def _wrap_result(self, op: Nu) -> Dict[K, V]:
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

    def _wrap_mapping_result(self, operand: Nu) -> Dict[K, V]:
        return Dict(operand)

    def __init__(
        self,
        address: StrArg | IntArg,
        *,
        value_type: type[V],
        key_type: type[K],
        key_value_type: type,
        value_value_type: type,
        parent_ref: RefBase | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(address, parent_ref=parent_ref, owner_shape=owner_shape)
        self._payload["value_type"] = value_type
        self._payload["key_type"] = key_type
        self._payload["key_value_type"] = key_value_type
        self._payload["value_value_type"] = value_value_type

    @classmethod
    def slot(cls, value_type: type[DV], key_type: type[DK] = str) -> DictRef[DK, DV]:  # type: ignore[assignment]
        """Declare a mapping slot with ``value_type`` values and ``key_type`` keys.

        Args:
            value_type: the Python type of the values held.
            key_type: the Python type of the keys. Defaults to ``str``.

        Notes:
            - The Nu Forms for both types are derived from them, so only the
              Python types are written.
            - ``meta: DictRef[str, int]`` as an annotation declares the same
              slot.

        Example:
            class Port(Shape):
                meta = DictRef.slot(int)
        """
        return Slot(
            cls,
            value_type=value_type,
            key_type=key_type,
            key_value_type=value_type_for(key_type),
            value_value_type=value_type_for(value_type),
        )  # type: ignore[return-value]

    @classmethod
    def _slot_kwargs_from_type_args(cls, args: tuple) -> dict[str, object]:
        """Derive slot kwargs from an annotation like ``DictRef[K, V]``."""
        key_type, value_type = args
        return {
            "value_type": value_type,
            "key_type": key_type,
            "key_value_type": value_type_for(key_type),
            "value_value_type": value_type_for(value_type),
        }
