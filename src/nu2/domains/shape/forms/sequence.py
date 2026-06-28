"""Shape-domain Sequence Form glue — tier-by-tier composition.

SequenceForm         = generic SequenceForm + shape CollectionForm
MutableSequenceForm  = generic MutableSequenceForm + shape MutableCollectionForm
ReactiveSequenceForm = generic ReactiveSequenceForm + shape MutableSequenceForm
                       + shape ReactiveCollectionForm

The Reactive tier brings together:
  - ``on_change()``           from generic ReactiveSequenceForm (generic)
  - ``on_child_change()`` etc from shape ReactiveCollectionForm (shape-domain)

v1 reference: ``src/nu/shapes/forms/abc/sequence.py``.
"""

from __future__ import annotations

from nu2.forms.collections.abc.sequence import MutableSequenceForm as _MutableSequenceForm
from nu2.forms.collections.abc.sequence import ReactiveSequenceForm as _ReactiveSequenceForm
from nu2.forms.collections.abc.sequence import SequenceForm as _SequenceForm

from .collection import CollectionForm, MutableCollectionForm, ReactiveCollectionForm


__all__ = [
    "MutableSequenceForm",
    "ReactiveSequenceForm",
    "SequenceForm",
]


class SequenceForm(_SequenceForm, CollectionForm):
    """Shape sequence — ordered-element ops + exists/missing/extract."""


class MutableSequenceForm(_MutableSequenceForm, MutableCollectionForm):
    """Mutable shape sequence — ordered-element ops + exists/missing/extract + store/erase."""


class ReactiveSequenceForm(_ReactiveSequenceForm, MutableSequenceForm, ReactiveCollectionForm):
    """Reactive shape sequence — adds on_change + tree-aware on_child_change* family.

    MRO provides:
        on_change()               from generic ReactiveSequenceForm
        on_child_change(addr)     from shape ReactiveCollectionForm
        on_children_change()      from shape ReactiveCollectionForm
        on_descendants_change(*)  from shape ReactiveCollectionForm
    """
