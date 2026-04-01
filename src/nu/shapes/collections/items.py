"""Item base hierarchy — typed values in a document model.

Three levels of capability:
    ItemBase         structural identity (typed value holder)
    MutableItemBase  + CRUD (get/set/delete/exists)
    ReactiveItemBase + change observation (on_change)

Substrates extend these with their own storage mechanisms.
"""

from __future__ import annotations

from nu import Value
from nu.shapes.capabilities import (
    ItemDeletableBase,
    ItemExistableBase,
    ItemSettableBase,
    PrimitiveObservableBase,
)


__all__ = [
    "ItemBase",
    "MutableItemBase",
    "ReactiveItemBase",
]


# =============================================================================
# ITEM BASE HIERARCHY
# =============================================================================


class ItemBase[T, ValueT: Value](
    ItemExistableBase,
):
    """Item in a document — holds a typed value.

    An item is the leaf node of the document model: a single typed value
    at an addressable location (e.g., a field in a shape, an element in
    a list, a value in a mapping).

    The ref itself IS the readable Nu — executing it reads the value
    via fetch()/coerce(). No separate load() needed.

    Provides:
        exists() -> BoolValue
        missing() -> BoolValue

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
    def value_value_type(self) -> type[ValueT]:
        """The Value class for this item's type."""
        return self._value_value_type


class MutableItemBase[T, ValueT: Value](
    ItemBase[T, ValueT],
    ItemSettableBase[T],
    ItemDeletableBase,
):
    """Item with mutable capabilities.

    Provides:
        immutable capabilities +
        store(value) -> typed Value
        erase() -> NoneValue
    """


class ReactiveItemBase[T, ValueT: Value](
    MutableItemBase[T, ValueT],
    PrimitiveObservableBase,
):
    """Item with CRUD + change observation.

    Provides everything from MutableItemBase plus:
        on_change() -> OnPrimitiveChangeOp
    """
