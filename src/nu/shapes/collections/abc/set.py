"""Set collection interfaces - three tiers for the document model.

SetLikeForm     = nu.forms.collections.abc.SetLikeForm + CollectionForm
MutableSetForm  = nu.forms.collections.abc.MutableSetForm + MutableCollectionI
ReactiveSetI = MutableSetForm + ReactiveCollectionI

Substrates implement _wrap_* methods and result() directly on their concrete refs.
"""

from __future__ import annotations

from nu.forms.collections.abc import MutableSetForm as _MutableSetI
from nu.forms.collections.abc import SetLikeForm as _SetLikeI

from .collection import CollectionForm, MutableCollectionI, ReactiveCollectionI


__all__ = [
    "MutableSetForm",
    "ReactiveSetI",
    "SetLikeForm",
]


class SetLikeForm[T, CollectionValueT, ElementValueT](
    _SetLikeI[set[T], T, CollectionValueT, ElementValueT],
    CollectionForm,
):
    """Set - unordered unique-element container in the document model."""


class MutableSetForm[T, CollectionValueT, ElementValueT](
    _MutableSetI[set[T], T, CollectionValueT, ElementValueT],
    MutableCollectionI[set[T]],
):
    """Mutable set - adds add, remove, discard, store, erase."""


class ReactiveSetI[T, CollectionValueT, ElementValueT](
    MutableSetForm[T, CollectionValueT, ElementValueT],
    ReactiveCollectionI[set[T]],
):
    """Reactive set - adds on_change, on_child_change, etc."""
