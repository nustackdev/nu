"""Sequence collection interfaces - three tiers for the document model.

SequenceForm         = nu.forms.collections.abc.SequenceForm + CollectionForm
MutableSequenceForm  = nu.forms.collections.abc.MutableSequenceForm + MutableCollectionI
ReactiveSequenceI = MutableSequenceForm + ReactiveCollectionI

Substrates implement _wrap_* methods and result() directly on their concrete refs.
"""

from __future__ import annotations

from nu.forms.collections.abc import MutableSequenceForm as _MutableSequenceI
from nu.forms.collections.abc import SequenceForm as _SequenceI

from .collection import CollectionForm, MutableCollectionI, ReactiveCollectionI


__all__ = [
    "MutableSequenceForm",
    "ReactiveSequenceI",
    "SequenceForm",
]


class SequenceForm[T, CollectionValueT, ItemValueT](
    _SequenceI[list[T], T, CollectionValueT, ItemValueT],
    CollectionForm,
):
    """Sequence - ordered container in the document model."""


class MutableSequenceForm[T, CollectionValueT, ItemValueT](
    _MutableSequenceI[list[T], T, CollectionValueT, ItemValueT],
    MutableCollectionI[list[T]],
):
    """Mutable sequence - adds append, extend, insert, pop, remove, store, erase."""


class ReactiveSequenceI[T, CollectionValueT, ItemValueT](
    MutableSequenceForm[T, CollectionValueT, ItemValueT],
    ReactiveCollectionI[list[T]],
):
    """Reactive sequence - adds on_change, on_child_change, etc."""
