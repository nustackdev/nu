# ruff: noqa: D102
"""Item base hierarchy - typed values in a document model.

Three tiers:
    ItemForm          exists(), missing()
    MutableItemForm   + store(), erase()
    ReactiveItemForm  + on_change()

Type Parameters:
    T:           Native Python type of the value (int, str, etc.)
    InterfaceT:  Form class for this item's type (IntForm, StrForm, etc.)

Substrates extend these with their own storage mechanisms.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.forms.primitives import BoolForm
from nu.terms import Form


if TYPE_CHECKING:
    from nu import Nu, Sentinel
    from nu.shapes.queries import OnChildChange


__all__ = [
    "ItemForm",
    "MutableItemForm",
    "ReactiveItemForm",
]


class ItemForm[T, InterfaceT](Form):
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
        """The Form class for this item's type."""
        return self._value_value_type

    def exists(self) -> BoolForm:
        from nu.shapes.queries import ItemExists

        return BoolForm(ItemExists(self))

    def missing(self) -> BoolForm:
        from nu.shapes.queries import ItemMissing

        return BoolForm(ItemMissing(self))


class MutableItemForm[T, InterfaceT](ItemForm[T, InterfaceT]):
    """Item with mutable capabilities.

    Provides:
        immutable capabilities +
        store(value) -> NoneForm
        erase() -> NoneForm
        init(default) -> Nu  (store if missing)
    """

    def store(self, value: T | Sentinel | Nu[T | Sentinel]) -> Nu:
        from nu.shapes.commands import ItemStoreCmd

        return ItemStoreCmd(self, value)

    def erase(self) -> Nu:
        from nu.shapes.commands import ItemEraseCmd

        return ItemEraseCmd(self)

    def init(self, default: T | Sentinel | Nu[T | Sentinel]) -> Nu:
        """Store default if value is missing. No-op if already set."""
        from nu.flows.control import IfDo

        return IfDo(self.missing(), self.store(default))


class ReactiveItemForm[T, InterfaceT](MutableItemForm[T, InterfaceT]):
    """Reactive item - CRUD + change observation."""

    def on_change(self) -> OnChildChange:
        from nu.shapes.queries import OnChildChange

        return OnChildChange(self.parent, self._raw_address)
