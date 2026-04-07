"""Item ref hierarchy - item bases + Ref navigation.

ItemRef         = ItemBase + Ref
MutableItemRef  = MutableItemBase + Ref
ReactiveItemRef = ReactiveItemBase + Ref

Type Parameters:
    T:           Native Python type of the value (int, str, etc.)
    InterfaceT:  Interface class for this item's type (IntI, StrI, etc.)
"""

from __future__ import annotations

from ..collections.abc import ItemBase, MutableItemBase, ReactiveItemBase
from .base import Ref


__all__ = [
    "ItemRef",
    "MutableItemRef",
    "ReactiveItemRef",
]


class ItemRef[T, InterfaceT](ItemBase[T, InterfaceT], Ref[T]):
    """Item ref - typed value holder with document-model navigation."""


class MutableItemRef[T, InterfaceT](MutableItemBase[T, InterfaceT], Ref[T]):
    """Mutable item ref - CRUD + navigation."""


class ReactiveItemRef[T, InterfaceT](ReactiveItemBase[T, InterfaceT], Ref[T]):
    """Reactive item ref - CRUD + observation + navigation."""
