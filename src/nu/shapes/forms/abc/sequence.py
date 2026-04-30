"""Sequence collection interfaces - three tiers for the document model.

SequenceForm         = nu.forms.collections.abc.SequenceForm + CollectionForm
MutableSequenceForm  = nu.forms.collections.abc.MutableSequenceForm + MutableCollectionForm
ReactiveSequenceForm = MutableSequenceForm + ReactiveCollectionForm

Substrates implement _wrap_* methods and result() directly on their concrete refs.
"""

from __future__ import annotations

from nu.forms.collections.abc import MutableSequenceForm as _MutableSequenceForm
from nu.forms.collections.abc import SequenceForm as _SequenceForm

from .collection import CollectionForm, MutableCollectionForm, ReactiveCollectionForm


__all__ = [
    "MutableSequenceForm",
    "ReactiveSequenceForm",
    "SequenceForm",
]


class SequenceForm[T, CollectionValueT, ItemValueT](
    _SequenceForm[list[T], T, CollectionValueT, ItemValueT],
    CollectionForm,
):
    """Sequence - ordered container in the document model."""


class MutableSequenceForm[T, CollectionValueT, ItemValueT](
    _MutableSequenceForm[list[T], T, CollectionValueT, ItemValueT],
    MutableCollectionForm[list[T]],
):
    """Mutable sequence - adds append, extend, insert, pop, remove, store, erase."""


class ReactiveSequenceForm[T, CollectionValueT, ItemValueT](
    MutableSequenceForm[T, CollectionValueT, ItemValueT],
    ReactiveCollectionForm[list[T]],
):
    """Reactive sequence - adds on_change, on_child_change, etc."""
