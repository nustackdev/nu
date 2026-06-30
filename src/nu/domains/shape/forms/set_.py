"""Shape-domain Set Form glue — tier-by-tier composition.

SetLikeForm     = generic SetLikeForm + shape CollectionForm
MutableSetForm  = generic MutableSetForm + shape MutableCollectionForm
ReactiveSetForm = generic ReactiveSetForm + shape MutableSetForm
                  + shape ReactiveCollectionForm

The Reactive tier brings together:
  - ``on_change()``           from generic ReactiveSetForm (generic)
  - ``on_child_change()`` etc from shape ReactiveCollectionForm (shape-domain)
"""

from __future__ import annotations

from nu.forms.collections.abc.set_ import MutableSetForm as _MutableSetForm
from nu.forms.collections.abc.set_ import ReactiveSetForm as _ReactiveSetForm
from nu.forms.collections.abc.set_ import SetLikeForm as _SetLikeForm

from .collection import CollectionForm, MutableCollectionForm, ReactiveCollectionForm


__all__ = [
    "MutableSetForm",
    "ReactiveSetForm",
    "SetLikeForm",
]


class SetLikeForm(_SetLikeForm, CollectionForm):
    """Shape set — unordered-unique-element ops + exists/missing/extract."""


class MutableSetForm(_MutableSetForm, MutableCollectionForm):
    """Mutable shape set — set ops + exists/missing/extract + store/erase."""


class ReactiveSetForm(_ReactiveSetForm, MutableSetForm, ReactiveCollectionForm):
    """Reactive shape set — adds on_change + tree-aware on_child_change* family.

    MRO provides:
        on_change()               from generic ReactiveSetForm
        on_child_change(addr)     from shape ReactiveCollectionForm
        on_children_change()      from shape ReactiveCollectionForm
        on_descendants_change(*)  from shape ReactiveCollectionForm
    """
