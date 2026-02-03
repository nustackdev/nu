"""Item ref hierarchy — typed values in a document model.

Three levels of capability:
    ItemRef         structural identity (typed value holder)
    MutableItemRef  + CRUD (get/set/delete/exists)
    ReactiveItemRef + change observation (on_change)

Substrates extend these with their own storage mechanisms.
"""

from __future__ import annotations

from everyabc import Value
from everyshape.capabilities import (
    ItemDeletableBase,
    ItemExistableBase,
    ItemGettableBase,
    ItemSettableBase,
    PrimitiveObservableBase,
)

from ..ref import Ref


__all__ = [
    "ItemRef",
    "MutableItemRef",
    "ReactiveItemRef",
]


# =============================================================================
# ITEM REF HIERARCHY
# =============================================================================


class ItemRef[T, ValueT: Value](Ref[T]):
    """Item in a document — holds a typed value.

    An item is the leaf node of the document model: a single typed value
    at an addressable location (e.g., a field in a shape, an element in
    a list, a value in a mapping).

    Substrates must provide:
        __init__: set _value_type and _value_value_type
        resolve(ctx): build location identity
        fetch(ctx): extract value
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


class MutableItemRef[T, ValueT: Value](
    ItemRef[T, ValueT],
    ItemExistableBase,
    ItemGettableBase[T],
    ItemSettableBase[T],
    ItemDeletableBase,
):
    """Item with CRUD capabilities.

    Provides:
        get() -> typed Value
        set(value) -> typed Value
        remove() -> NoneValue
        exists() -> BoolValue
        missing() -> BoolValue
    """


class ReactiveItemRef[T, ValueT: Value](
    MutableItemRef[T, ValueT],
    PrimitiveObservableBase,
):
    """Item with CRUD + change observation.

    Provides everything from MutableItemRef plus:
        on_change() -> OnPrimitiveChangeOp
    """
