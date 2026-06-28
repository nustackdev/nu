"""SequenceRef hierarchy — ordered container Ref + Form mixin tiers.

    SequenceRef         = shape.SequenceForm + _StructuredRef
    MutableSequenceRef  = shape.MutableSequenceForm + SequenceRef
    ReactiveSequenceRef = shape.ReactiveSequenceForm + MutableSequenceRef

shape.SequenceForm already composes generic SequenceForm + shape CollectionForm,
so exists()/missing()/extract()/store()/erase() are all present without a
separate ItemForm in the MRO.

Subscript access (``ref[i]``) returns the matching-tier ItemRef.

Form composition provides:
    base:     len(), contains(), iter(), [i], first_elem(), last_elem(), ...,
              exists(), missing(), extract()
    mutable:  + append(v), extend(), insert(i,v), pop(), ..., store(v), erase()
    reactive: + on_change() (generic), on_child_change(), on_children_change(),
                on_descendants_change() (shape-domain)

The ``_wrap_*`` abstract methods from SequenceForm are left un-overridden
(raise NotImplementedError) in these blueprints — substrate subclasses fill
them in.

v1 reference: ``src/nu/shapes/refs/sequence.py``.
"""

from __future__ import annotations

from nu2.domains.shape.forms.sequence import MutableSequenceForm, ReactiveSequenceForm, SequenceForm

from .base import _StructuredRef
from .item import ItemRef, MutableItemRef, ReactiveItemRef


__all__ = [
    "MutableSequenceRef",
    "ReactiveSequenceRef",
    "SequenceRef",
]


class SequenceRef(SequenceForm, _StructuredRef):
    """Ordered container Ref.

    ``ref[i]`` returns an ItemRef (immutable view of the element at index).
    SequenceForm surface (len, first_elem, last_elem, exists, missing, ...) is
    available; methods that require _wrap_* overrides raise NotImplementedError
    on this blueprint.
    """

    def __getitem__(self, index: object) -> ItemRef:
        """Return an ItemRef at index, with self as parent."""
        return ItemRef(index, parent_ref=self, owner_shape=self._owner_shape)


class MutableSequenceRef(MutableSequenceForm, SequenceRef):
    """Mutable ordered container Ref.

    ``ref[i]`` returns a MutableItemRef.
    Adds: append(v), extend(), insert(i,v), pop(), ..., store(v), erase().
    """

    def __getitem__(self, index: object) -> MutableItemRef:
        """Return a MutableItemRef at index, with self as parent."""
        return MutableItemRef(index, parent_ref=self, owner_shape=self._owner_shape)


class ReactiveSequenceRef(ReactiveSequenceForm, MutableSequenceRef):
    """Reactive ordered container Ref.

    ``ref[i]`` returns a ReactiveItemRef.
    Adds: on_change(), on_child_change(), on_children_change(),
    on_descendants_change() on top of MutableSequenceRef.
    """

    def __getitem__(self, index: object) -> ReactiveItemRef:
        """Return a ReactiveItemRef at index, with self as parent."""
        return ReactiveItemRef(index, parent_ref=self, owner_shape=self._owner_shape)
