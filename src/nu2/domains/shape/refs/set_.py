"""SetRef hierarchy — unordered unique-element container Ref + Form mixin tiers.

    SetRef         = shape.SetLikeForm + _StructuredRef
    MutableSetRef  = shape.MutableSetForm + SetRef
    ReactiveSetRef = shape.ReactiveSetForm + MutableSetRef

shape.SetLikeForm already composes generic SetLikeForm + shape CollectionForm,
so exists()/missing()/extract()/store()/erase() are all present without a
separate ItemForm in the MRO.

Sets have no subscript navigation (no child descent); semantics are membership
and set-algebra. Slot-level operations still apply.

Form composition provides:
    base:     len(), contains(), iter(), union(), intersection(), ...,
              exists(), missing(), extract()
    mutable:  + add(v), remove(v), discard(v), pop(), ..., store(v), erase()
    reactive: + on_change() (generic), on_child_change(), on_children_change(),
                on_descendants_change() (shape-domain)

The ``_wrap_*`` abstract methods from SetLikeForm are left un-overridden
(raise NotImplementedError) in these blueprints — substrate subclasses fill
them in.

v1 reference: ``src/nu/shapes/refs/set.py``.
"""

from __future__ import annotations

from nu2.domains.shape.forms.set_ import MutableSetForm, ReactiveSetForm, SetLikeForm

from .base import _StructuredRef


__all__ = [
    "MutableSetRef",
    "ReactiveSetRef",
    "SetRef",
]


class SetRef(SetLikeForm, _StructuredRef):
    """Unordered unique-element container Ref; no child descent.

    SetLikeForm surface (len, contains, union, intersection, exists, missing, ...)
    is available; methods that require _wrap_* overrides raise NotImplementedError
    on this blueprint.
    """


class MutableSetRef(MutableSetForm, SetRef):
    """Mutable unordered unique-element container Ref.

    Adds: add(v), remove(v), discard(v), pop(), update(), ..., store(v), erase().
    """


class ReactiveSetRef(ReactiveSetForm, MutableSetRef):
    """Reactive unordered unique-element container Ref.

    Adds: on_change(), on_child_change(), on_children_change(),
    on_descendants_change() on top of MutableSetRef.
    """
