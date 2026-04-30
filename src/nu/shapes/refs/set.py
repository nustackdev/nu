"""Set ref hierarchy — set bases + Ref navigation.

SetLikeRef     = SetLikeForm + Ref
MutableSetRef  = MutableSetForm + Ref
ReactiveSetRef = ReactiveSetForm + Ref

Sets have no child ref navigation (no subscript access) — only
collection-level operations (union, intersection, add, remove, etc.).

Type Parameters:
    T:               Native element type (int, str, etc.)
    CollectionValueT: Wrapped result for collection-level ops (union, intersection, store)
    ElementValueT:    Wrapped result for element-level ops (sum_, min_, max_)
"""

from __future__ import annotations

from nu.shapes.forms import MutableSetForm, ReactiveSetForm, SetLikeForm

from .base import Ref


__all__ = [
    "MutableSetRef",
    "ReactiveSetRef",
    "SetLikeRef",
]


class SetLikeRef[T, CollectionValueT, ElementValueT](
    SetLikeForm[T, CollectionValueT, ElementValueT],
    Ref[set[T]],
):
    """Set ref — unordered unique-element container with document-model navigation."""


class MutableSetRef[T, CollectionValueT, ElementValueT](
    MutableSetForm[T, CollectionValueT, ElementValueT],
    SetLikeRef[T, CollectionValueT, ElementValueT],
):
    """Mutable set ref — add/remove/discard + navigation."""


class ReactiveSetRef[T, CollectionValueT, ElementValueT](
    ReactiveSetForm[T, CollectionValueT, ElementValueT],
    MutableSetRef[T, CollectionValueT, ElementValueT],
):
    """Reactive set ref — observation + mutations + navigation."""
