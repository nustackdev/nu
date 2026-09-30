"""Set family: an unordered collection of unique elements in a shape fabric.

Forms weave the Python set surface with the shape collection ops, tier by tier,
and type every result by what the slot declared: an element reads as the
declared value's form, and set algebra carries the declared element type on.

Refs bind that surface to an address. A set has no keys, so there is no descent.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.forms.collections.abc.set_ import MutableSetForm as _MutableSetForm
from nu.forms.collections.abc.set_ import ReactiveSetForm as _ReactiveSetForm
from nu.forms.collections.abc.set_ import SetLikeForm as _SetLikeForm

from .base import StructuredRef
from .collection import (
    CollectionForm,
    MutableCollectionForm,
    ReactiveCollectionForm,
    form_of,
    holding,
)


if TYPE_CHECKING:
    from nu.forms import Iterator, Set
    from nu.lang import Form, Nu


__all__ = [
    "MutableSetForm",
    "MutableSetRef",
    "ReactiveSetForm",
    "ReactiveSetRef",
    "SetLikeForm",
    "SetRef",
]


class SetLikeForm(_SetLikeForm, CollectionForm):
    """Shape set: unordered-unique-element ops + exists/missing/extract, typed by the declaration."""

    def _wrap_element_result(self, operand: Nu) -> Form:
        return form_of(self._declared.elem)(operand)  # type: ignore[return-value]

    def iter(self) -> Iterator:
        """A lazy stream over its elements, typed by the declared value."""
        from nu.core import Iter

        return self._wrap_iterable_result(Iter(self))

    def _wrap_iterable_result(self, operand: Nu) -> Iterator:
        from collections.abc import Iterator as PyIterator

        from nu.forms import Iterator

        return holding(Iterator(operand), PyIterator, elem=self._declared.elem)

    def _wrap_set_result(self, operand: Nu) -> Set:
        from nu.forms import Set

        return holding(Set(operand), set, elem=self._declared.elem)


class MutableSetForm(_MutableSetForm, MutableCollectionForm):
    """Mutable shape set: set ops + exists/missing/extract + set/erase."""


class ReactiveSetForm(_ReactiveSetForm, MutableSetForm, ReactiveCollectionForm):
    """Reactive shape set. Adds on_change + tree-aware on_child_change* family.

    MRO provides:
        on_change()               from generic ReactiveSetForm
        on_child_change(addr)     from shape ReactiveCollectionForm
        on_children_change()      from shape ReactiveCollectionForm
        on_descendants_change(*)  from shape ReactiveCollectionForm
    """


class SetRef(SetLikeForm, StructuredRef):
    """Unordered unique-element container Ref; no child descent."""


class MutableSetRef(MutableSetForm, SetRef):
    """Mutable unordered unique-element container Ref.

    Adds: add(v), remove(v), discard(v), pop(), update(), ..., store(v), erase().
    """


class ReactiveSetRef(ReactiveSetForm, MutableSetRef):
    """Reactive unordered unique-element container Ref.

    Adds: on_change(), on_child_change(), on_children_change(),
    on_descendants_change() on top of MutableSetRef.
    """
