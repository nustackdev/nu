"""Item ref hierarchy — item bases + Ref navigation.

ItemRef         = ItemBase + Ref
MutableItemRef  = MutableItemBase + ItemRef
ReactiveItemRef = ReactiveItemBase + MutableItemRef

Type Parameters:
    T:      Native Python type of the value (int, str, etc.)
    ValueT: Wrapped Value class for this item's type (IntValue, StrValue, etc.) — Value subclass
"""

from __future__ import annotations

from nu import Value
from nu.shapes.collections import ItemBase, MutableItemBase, ReactiveItemBase

from .base import Ref


__all__ = [
    "ItemRef",
    "MutableItemRef",
    "ReactiveItemRef",
]


class ItemRef[T, ValueT: Value](ItemBase[T, ValueT], Ref[T]):
    """Item ref — typed value holder with document-model navigation."""


class MutableItemRef[T, ValueT: Value](MutableItemBase[T, ValueT], Ref[T]):
    """Mutable item ref — CRUD + navigation."""


class ReactiveItemRef[T, ValueT: Value](ReactiveItemBase[T, ValueT], Ref[T]):
    """Reactive item ref — CRUD + observation + navigation."""
