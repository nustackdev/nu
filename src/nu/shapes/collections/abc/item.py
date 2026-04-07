# ruff: noqa: D102
"""Item base hierarchy - typed values in a document model.

Three tiers:
    ItemI          exists(), missing()
    MutableItemI   + store(), erase()
    ReactiveItemI  + on_change()

Type Parameters:
    T:           Native Python type of the value (int, str, etc.)
    InterfaceT:  Interface class for this item's type (IntI, StrI, etc.)

Substrates extend these with their own storage mechanisms.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.primitives import BoolI, NoneI


if TYPE_CHECKING:
    from nu import Nu, Sentinel

    from ...ops.reactive import OnPrimitiveChangeOp


__all__ = [
    "ItemI",
    "MutableItemI",
    "ReactiveItemI",
]


class ItemI[T, InterfaceT]:
    """Item in a document - holds a typed value.

    An item is the leaf node of the document model: a single typed value
    at an addressable location (e.g., a field in a shape, an element in
    a list, a value in a mapping).

    The ref itself IS the readable Nu - executing it reads the value
    via fetch()/coerce(). No separate load() needed.

    Substrates must provide:
        __init__: set _value_type and _value_value_type
        resolve(ctx): build location identity
        fetch(ctx): extract value (calls coerce() for type conversion)
        fetch_parent(ctx): get parent collection
        resolve_address(ctx): get address within parent
    """

    @property
    def value_type(self) -> type[T]:
        """The Python type of the value at this location."""
        return self._value_type

    @property
    def interface_cls(self) -> type[InterfaceT]:
        """The Interface class for this item's type."""
        return self._value_value_type

    def exists(self) -> BoolI:
        from nu.shapes.ops.item import ItemExistsOp

        return BoolI(ItemExistsOp(self))

    def missing(self) -> BoolI:
        from nu.shapes.ops.item import ItemMissingOp

        return BoolI(ItemMissingOp(self))


class MutableItemI[T, InterfaceT](ItemI[T, InterfaceT]):
    """Item with mutable capabilities.

    Provides:
        immutable capabilities +
        store(value) -> NoneI
        erase() -> NoneI
    """

    def store(self, value: T | Sentinel | Nu[T | Sentinel]) -> NoneI:
        from nu.utils import ensure_nu

        from nu.shapes.ops.item import ItemStoreCmd

        return NoneI(ItemStoreCmd(self, ensure_nu(value)))

    def erase(self) -> NoneI:
        from nu.shapes.ops.item import ItemEraseCmd

        return NoneI(ItemEraseCmd(self))


class ReactiveItemI[T, InterfaceT](MutableItemI[T, InterfaceT]):
    """Reactive item - CRUD + change observation."""

    def on_change(self) -> OnPrimitiveChangeOp:
        from nu.shapes.ops.reactive import OnPrimitiveChangeOp

        return OnPrimitiveChangeOp(self)
