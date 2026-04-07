"""Item ref hierarchy - item interfaces + Ref navigation.

ItemRef         = ItemI + Ref
MutableItemRef  = MutableItemI + Ref
ReactiveItemRef = ReactiveItemI + Ref

Type Parameters:
    T:           Native Python type of the value (int, str, etc.)
    InterfaceT:  Interface class for this item's type (IntI, StrI, etc.)
"""

from __future__ import annotations

from nu.shapes.collections import ItemI, MutableItemI, ReactiveItemI
from .base import Ref


__all__ = [
    "ItemRef",
    "MutableItemRef",
    "ReactiveItemRef",
]


class ItemRef[T, InterfaceT](ItemI[T, InterfaceT], Ref[T]):
    """Item ref - typed value holder with document-model navigation."""


class MutableItemRef[T, InterfaceT](MutableItemI[T, InterfaceT], Ref[T]):
    """Mutable item ref - CRUD + navigation."""


class ReactiveItemRef[T, InterfaceT](ReactiveItemI[T, InterfaceT], Ref[T]):
    """Reactive item ref - CRUD + observation + navigation."""
