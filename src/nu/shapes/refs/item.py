"""Item ref hierarchy - item interfaces + Ref navigation.

ItemRef         = ItemForm + Ref
MutableItemRef  = MutableItemForm + Ref
ReactiveItemRef = ReactiveItemForm + Ref

Type Parameters:
    T:           Native Python type of the value (int, str, etc.)
    InterfaceT:  Form class for this item's type (IntForm, StrForm, etc.)
"""

from __future__ import annotations

from nu.shapes.forms import ItemForm, MutableItemForm, ReactiveItemForm

from .base import Ref


__all__ = [
    "ItemRef",
    "MutableItemRef",
    "ReactiveItemRef",
]


class ItemRef[T, InterfaceT](ItemForm[T, InterfaceT], Ref[T]):
    """Item ref - typed value holder with document-model navigation."""


class MutableItemRef[T, InterfaceT](MutableItemForm[T, InterfaceT], Ref[T]):
    """Mutable item ref - CRUD + navigation."""


class ReactiveItemRef[T, InterfaceT](ReactiveItemForm[T, InterfaceT], Ref[T]):
    """Reactive item ref - CRUD + observation + navigation."""
