"""Shape-domain Form chain.

Re-exports all shape Form tiers across all families:

Item trunk (no generic peer):
    ItemForm / MutableItemForm / ReactiveItemForm

Collection trunk (base + mutable + reactive):
    CollectionForm / MutableCollectionForm / ReactiveCollectionForm

Glue tiers (compose generic + shape per tier):
    MappingForm / MutableMappingForm / ReactiveMappingForm
    SequenceForm / MutableSequenceForm / ReactiveSequenceForm
    SetLikeForm / MutableSetForm / ReactiveSetForm
"""

from __future__ import annotations

from .collection import CollectionForm, MutableCollectionForm, ReactiveCollectionForm
from .item import ItemForm, MutableItemForm, ReactiveItemForm
from .mapping import MappingForm, MutableMappingForm, ReactiveMappingForm
from .sequence import MutableSequenceForm, ReactiveSequenceForm, SequenceForm
from .set_ import MutableSetForm, ReactiveSetForm, SetLikeForm


__all__ = [
    "CollectionForm",
    "ItemForm",
    "MappingForm",
    "MutableCollectionForm",
    "MutableItemForm",
    "MutableMappingForm",
    "MutableSequenceForm",
    "MutableSetForm",
    "ReactiveCollectionForm",
    "ReactiveItemForm",
    "ReactiveMappingForm",
    "ReactiveSequenceForm",
    "ReactiveSetForm",
    "SequenceForm",
    "SetLikeForm",
]
