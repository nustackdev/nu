"""Sequence family: an ordered collection in a shape fabric.

Forms weave the Python sequence surface with the shape collection ops, tier by
tier, and type every result by what the slot declared: an element reads as the
declared value's form, and a slice carries the declared element type on.

Refs add descent. ``ref[i]`` is the child ref at that position, built by the
fabric from the declared value; a slice stays a value.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.forms.collections.abc.sequence import MutableSequenceForm as _MutableSequenceForm
from nu.forms.collections.abc.sequence import ReactiveSequenceForm as _ReactiveSequenceForm
from nu.forms.collections.abc.sequence import SequenceForm as _SequenceForm

from .base import StructuredRef
from .collection import (
    CollectionForm,
    MutableCollectionForm,
    ReactiveCollectionForm,
    form_of,
    holding,
)


if TYPE_CHECKING:
    from nu.forms import Iterator, List
    from nu.lang import Form, Nu


__all__ = [
    "MutableSequenceForm",
    "MutableSequenceRef",
    "ReactiveSequenceForm",
    "ReactiveSequenceRef",
    "SequenceForm",
    "SequenceRef",
]


class SequenceForm(_SequenceForm, CollectionForm):
    """Shape sequence: ordered-element ops + exists/missing/extract, typed by the declaration."""

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

    def _wrap_sliceable_result(self, operand: Nu) -> List:
        from nu.forms import List

        return holding(List(operand), list, elem=self._declared.elem)


class MutableSequenceForm(_MutableSequenceForm, MutableCollectionForm):
    """Mutable shape sequence: ordered-element ops + exists/missing/extract + set/erase."""


class ReactiveSequenceForm(_ReactiveSequenceForm, MutableSequenceForm, ReactiveCollectionForm):
    """Reactive shape sequence. Adds on_change + tree-aware on_child_change* family.

    MRO provides:
        on_change()               from generic ReactiveSequenceForm
        on_child_change(addr)     from shape ReactiveCollectionForm
        on_children_change()      from shape ReactiveCollectionForm
        on_descendants_change(*)  from shape ReactiveCollectionForm
    """


class SequenceRef(SequenceForm, StructuredRef):
    """Ordered container Ref; ``ref[i]`` navigates to the element's child Ref.

    Navigation is defined once here and routes through ``_wrap_item_ref``, the
    one hook that returns a ref rather than a form. It is a substrate plug-point
    on ``StructuredRef``: the child is always a fabric's own ref, so the fabric's
    substrate base supplies it, and a fabric that leaves it out fails loudly.
    """

    def __getitem__(self, index: object) -> StructuredRef:
        """Int index navigates to the child Ref; slice routes to the form-level slice op."""
        if isinstance(index, slice):
            return self.slice(index.start, index.stop, index.step)  # type: ignore[return-value]
        return self._wrap_item_ref(index)


class MutableSequenceRef(MutableSequenceForm, SequenceRef):
    """Mutable ordered container Ref.

    Adds: append(v), extend(), insert(i,v), pop(), ..., store(v), erase().
    """


class ReactiveSequenceRef(ReactiveSequenceForm, MutableSequenceRef):
    """Reactive ordered container Ref.

    Adds: on_change(), on_child_change(), on_children_change(),
    on_descendants_change() on top of MutableSequenceRef.
    """
