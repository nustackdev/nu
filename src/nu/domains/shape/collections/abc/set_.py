"""Set row: an unordered collection of unique elements in a shape fabric, at the ABC level.

Three tiers over ``SetLikeForm`` (the ``collections.abc.Set`` form). A tier is
the capability base first, then the tier below, then the ``nu.forms`` set ABC of
that tier, so the shape typing and slot ops win over the plain form's. Every
result is typed by what the slot declared: an element reads as the declared
value's form, and set algebra carries the declared element type on.

Refs bind that surface to an address. A set has no keys, so there is no descent.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.forms.collections.abc.set_ import MutableSetForm as _MutableSetForm
from nu.forms.collections.abc.set_ import ReactiveSetForm as _ReactiveSetForm
from nu.forms.collections.abc.set_ import SetLikeForm as _SetLikeForm

from ...base import StructuredRef
from ...collection import (
    CollectionForm,
    MutableCollectionForm,
    ReactiveCollectionForm,
    form_of,
    holding,
)


if TYPE_CHECKING:
    from nu.forms import Iterator
    from nu.forms.primitives import Object
    from nu.lang import Nu


__all__ = [
    "MutableSetForm",
    "MutableSetRef",
    "ReactiveSetForm",
    "ReactiveSetRef",
    "SetLikeForm",
    "SetRef",
]


class SetLikeForm(CollectionForm, _SetLikeForm):
    """Shape set: unordered-unique-element ops + exists/extract, typed by the declaration."""

    def _wrap_element_result(self, operand: Nu) -> Object:
        return form_of(self._declared.elem)(operand)  # type: ignore[return-value]

    def _wrap_iterable_result(self, operand: Nu) -> Iterator:
        """A stream over its elements (``iter``), typed by the declaration."""
        from collections.abc import Iterator as PyIterator

        from nu.forms import Iterator

        return holding(Iterator(operand), PyIterator, elem=self._declared.elem)

    def _wrap_set_result(self, operand: Nu) -> _SetLikeForm:
        """Set algebra: a Set carrying the declared element type on. A row narrows it to its own type."""
        from nu.forms import Set

        return holding(Set(operand), set, elem=self._declared.elem)


class MutableSetForm(MutableCollectionForm, SetLikeForm, _MutableSetForm):
    """Mutable shape set: set ops + exists/extract + set/erase."""


class ReactiveSetForm(ReactiveCollectionForm, MutableSetForm, _ReactiveSetForm):
    """Reactive shape set: adds on_change and the tree-aware on_child_change family."""


class SetRef(SetLikeForm, StructuredRef):
    """Unordered unique-element container Ref; no child descent."""


class MutableSetRef(MutableSetForm, SetRef):
    """Mutable unordered unique-element container Ref.

    Adds: add(v), remove(v), discard(v), pop(), clear(), update(), ..., set(v), erase().
    """


class ReactiveSetRef(ReactiveSetForm, MutableSetRef):
    """Reactive unordered unique-element container Ref.

    Adds: on_change(), on_child_change(), on_children_change(),
    on_descendants_change() on top of MutableSetRef.
    """
