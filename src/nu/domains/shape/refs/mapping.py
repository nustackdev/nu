"""MappingRef hierarchy — key-value container Ref + Form mixin tiers.

    MappingRef         = shape.MappingForm + StructuredRef
    MutableMappingRef  = shape.MutableMappingForm + MappingRef
    ReactiveMappingRef = shape.ReactiveMappingForm + MutableMappingRef

shape.MappingForm already composes generic MappingForm + shape CollectionForm,
so exists()/missing()/extract()/store()/erase() are all present without a
separate ItemForm in the MRO.

Subscript access (``ref[key]``) returns the matching-tier ItemRef.

Form composition provides:
    base:     len(), contains(), iter(), keys(), values(), items(), [k],
              exists(), missing(), extract()
    mutable:  + set(k,v), delete(k), update(), ..., store(v), erase()
    reactive: + on_change(), on_child_change(), on_children_change(),
                on_descendants_change()

The ``_wrap_*`` abstract methods from MappingForm are left un-overridden
(raise NotImplementedError) in these blueprints — substrate subclasses fill
them in.
"""

from __future__ import annotations

from nu.domains.shape.forms.mapping import MappingForm, MutableMappingForm, ReactiveMappingForm

from .base import StructuredRef
from .item import ItemRef, MutableItemRef, ReactiveItemRef


__all__ = [
    "MappingRef",
    "MutableMappingRef",
    "ReactiveMappingRef",
]


class MappingRef(MappingForm, StructuredRef):
    """Key-value container Ref.

    ``ref[key]`` returns an ItemRef (immutable view of the value at key).
    MappingForm surface (len, keys, values, items, exists, missing, ...) is
    available; methods that require _wrap_* overrides raise NotImplementedError
    on this blueprint.
    """

    def __getitem__(self, key: object) -> ItemRef:
        """Return an ItemRef at key, with self as parent."""
        return ItemRef(key, parent_ref=self, owner_shape=self._owner_shape)


class MutableMappingRef(MutableMappingForm, MappingRef):
    """Mutable key-value container Ref.

    ``ref[key]`` returns a MutableItemRef.
    Adds: set(k,v), delete(k), update(), store(v), erase() on top of MappingRef.
    """

    def __getitem__(self, key: object) -> MutableItemRef:
        """Return a MutableItemRef at key, with self as parent."""
        return MutableItemRef(key, parent_ref=self, owner_shape=self._owner_shape)


class ReactiveMappingRef(ReactiveMappingForm, MutableMappingRef):
    """Reactive key-value container Ref.

    ``ref[key]`` returns a ReactiveItemRef.
    Adds: on_change() (generic), on_child_change(), on_children_change(),
    on_descendants_change() (shape-domain) on top of MutableMappingRef.
    """

    def __getitem__(self, key: object) -> ReactiveItemRef:
        """Return a ReactiveItemRef at key, with self as parent."""
        return ReactiveItemRef(key, parent_ref=self, owner_shape=self._owner_shape)
