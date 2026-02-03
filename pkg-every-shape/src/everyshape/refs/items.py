"""Item ref hierarchy — item bases + Ref navigation.

ItemRef         = ItemBase + Ref
MutableItemRef  = MutableItemBase + ItemRef
ReactiveItemRef = ReactiveItemBase + MutableItemRef
"""

from __future__ import annotations

from everybase import Value
from everyshape.collections import ItemBase, MutableItemBase, ReactiveItemBase

from .base import Ref


__all__ = [
    "ItemRef",
    "MutableItemRef",
    "ReactiveItemRef",
]


class ItemRef[T, ValueT: Value](ItemBase[T, ValueT], Ref[T]):
    """Item ref — typed value holder with document-model navigation."""


class MutableItemRef[T, ValueT: Value](MutableItemBase[T, ValueT], ItemRef[T, ValueT]):
    """Mutable item ref — CRUD + navigation."""


class ReactiveItemRef[T, ValueT: Value](ReactiveItemBase[T, ValueT], MutableItemRef[T, ValueT]):
    """Reactive item ref — CRUD + observation + navigation."""
