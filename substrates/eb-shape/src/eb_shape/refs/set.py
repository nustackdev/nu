"""Set ref hierarchy — set bases + Ref navigation.

SetLikeRefBase     = SetLikeBase + Ref
MutableSetRefBase  = MutableSetBase + Ref
ReactiveSetRefBase = ReactiveSetBase + Ref

Sets have no child ref navigation (no subscript access) — only
collection-level operations (union, intersection, add, remove, etc.).

Type Parameters:
    T:               Native element type (int, str, etc.)
    CollectionValueT: Wrapped result for collection-level ops (union, intersection, store)
    ElementValueT:    Wrapped result for element-level ops (sum_, min_, max_)
"""

from __future__ import annotations

from eb_shape.collections import MutableSetBase, ReactiveSetBase, SetLikeBase

from .base import Ref


__all__ = [
    "MutableSetRefBase",
    "ReactiveSetRefBase",
    "SetLikeRefBase",
]


class SetLikeRefBase[T, CollectionValueT, ElementValueT](
    SetLikeBase[T, CollectionValueT, ElementValueT],
    Ref[set[T]],
):
    """Set ref — unordered unique-element container with document-model navigation."""


class MutableSetRefBase[T, CollectionValueT, ElementValueT](
    MutableSetBase[T, CollectionValueT, ElementValueT],
    SetLikeRefBase[T, CollectionValueT, ElementValueT],
):
    """Mutable set ref — add/remove/discard + navigation."""


class ReactiveSetRefBase[T, CollectionValueT, ElementValueT](
    ReactiveSetBase[T, CollectionValueT, ElementValueT],
    MutableSetRefBase[T, CollectionValueT, ElementValueT],
):
    """Reactive set ref — observation + mutations + navigation."""
