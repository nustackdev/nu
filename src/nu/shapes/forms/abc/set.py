"""Set collection interfaces - three tiers for the document model.

SetLikeForm     = nu.forms.collections.abc.SetLikeForm + CollectionForm
MutableSetForm  = nu.forms.collections.abc.MutableSetForm + MutableCollectionForm
ReactiveSetForm = MutableSetForm + ReactiveCollectionForm

Substrates implement _wrap_* methods and result() directly on their concrete refs.
"""

from __future__ import annotations

from nu.forms.collections.abc import MutableSetForm as _MutableSetForm
from nu.forms.collections.abc import SetLikeForm as _SetLikeForm

from .collection import CollectionForm, MutableCollectionForm, ReactiveCollectionForm


__all__ = [
    "MutableSetForm",
    "ReactiveSetForm",
    "SetLikeForm",
]


class SetLikeForm[T, CollectionValueT, ElementValueT](
    _SetLikeForm[set[T], T, CollectionValueT, ElementValueT],
    CollectionForm,
):
    """Set - unordered unique-element container in the document model."""


class MutableSetForm[T, CollectionValueT, ElementValueT](
    _MutableSetForm[set[T], T, CollectionValueT, ElementValueT],
    MutableCollectionForm[set[T]],
):
    """Mutable set - adds add, remove, discard, store, erase."""


class ReactiveSetForm[T, CollectionValueT, ElementValueT](
    MutableSetForm[T, CollectionValueT, ElementValueT],
    ReactiveCollectionForm[set[T]],
):
    """Reactive set - adds on_change, on_child_change, etc."""
