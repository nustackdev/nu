"""ItemRef hierarchy — leaf Ref + Form mixin tiers.

    ItemRef         = ItemForm + StructuredRef
    MutableItemRef  = MutableItemForm + ItemRef
    ReactiveItemRef = ReactiveItemForm + MutableItemRef

A leaf Ref names a single typed value — no child descent.
The Form mixins provide the slot-level API:
    base:     exists(), missing()
    mutable:  + store(), erase()
    reactive: + on_change()
"""

from __future__ import annotations

from nu.domains.shape.forms.item import ItemForm, MutableItemForm, ReactiveItemForm

from .base import StructuredRef


__all__ = [
    "ItemRef",
    "MutableItemRef",
    "ReactiveItemRef",
]


class ItemRef(ItemForm, StructuredRef):
    """Leaf Ref — single typed value, no child descent.

    API: exists(), missing() (from ItemForm).
    """


class MutableItemRef(MutableItemForm, ItemRef):
    """Mutable leaf Ref — single typed value with write/erase.

    API: exists(), missing(), store(v), erase() (from MutableItemForm).
    """


class ReactiveItemRef(ReactiveItemForm, MutableItemRef):
    """Reactive leaf Ref — single typed value with observation.

    API: exists(), missing(), store(v), erase(), on_change() (from ReactiveItemForm).
    """
