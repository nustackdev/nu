"""Mapping rows: a key-value collection in a shape fabric, at the ABC level.

Two rows, ``Mapping`` and ``OrderedMapping`` (Mapping + Reversible), each in
three tiers. A tier is the capability base first, then the tier below, then the
``nu.forms`` mapping ABC of that tier, so the shape typing and slot ops win
over the plain form's. Every result is typed by what the slot declared: a value
reads as the declared value's form, and keys, values and items carry the
declared types on.

Refs add descent. ``ref[key]`` is the child ref at that key, built by the
fabric from the declared value, because only the fabric knows which of its
refs holds that value.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.forms.collections.abc.mapping import MappingForm as _MappingForm
from nu.forms.collections.abc.mapping import MutableMappingForm as _MutableMappingForm
from nu.forms.collections.abc.mapping import (
    MutableOrderedMappingForm as _MutableOrderedMappingForm,
)
from nu.forms.collections.abc.mapping import OrderedMappingForm as _OrderedMappingForm
from nu.forms.collections.abc.mapping import ReactiveMappingForm as _ReactiveMappingForm
from nu.forms.collections.abc.mapping import (
    ReactiveOrderedMappingForm as _ReactiveOrderedMappingForm,
)

from ...base import StructuredRef
from ...collection import (
    CollectionForm,
    MutableCollectionForm,
    ReactiveCollectionForm,
    form_of,
    holding,
)


if TYPE_CHECKING:
    from nu.forms import DictItems, DictKeys, DictValues, Iterator, List
    from nu.forms.primitives import Object
    from nu.lang import Nu


__all__ = [
    "MappingForm",
    "MappingRef",
    "MutableMappingForm",
    "MutableMappingRef",
    "MutableOrderedMappingForm",
    "MutableOrderedMappingRef",
    "OrderedMappingForm",
    "OrderedMappingRef",
    "ReactiveMappingForm",
    "ReactiveMappingRef",
    "ReactiveOrderedMappingForm",
    "ReactiveOrderedMappingRef",
]


class MappingForm(CollectionForm, _MappingForm):
    """Shape mapping: key-value ops + exists/extract, typed by the declaration."""

    def _wrap_value_result(self, operand: Nu) -> Object:
        return form_of(self._declared.elem)(operand)  # type: ignore[return-value]

    def _wrap_element_result(self, operand: Nu) -> Object:
        return form_of(self._declared.key)(operand)  # type: ignore[return-value]

    def _wrap_iterable_result(self, operand: Nu) -> Iterator:
        """A stream over its keys (``iter``), typed by the declaration."""
        from collections.abc import Iterator as PyIterator

        from nu.forms import Iterator

        return holding(Iterator(operand), PyIterator, elem=self._declared.key)

    def _wrap_keys_result(self, operand: Nu) -> DictKeys:
        from nu.forms import DictKeys

        return holding(DictKeys(operand), set, elem=self._declared.key)

    def _wrap_values_result(self, operand: Nu) -> DictValues:
        from nu.forms import DictValues

        return holding(DictValues(operand), list, elem=self._declared.elem)

    def _wrap_items_result(self, operand: Nu) -> DictItems:
        from nu.forms import DictItems

        declared = self._declared
        return holding(DictItems(operand), dict, key=declared.key, elem=declared.elem)


class MutableMappingForm(MutableCollectionForm, MappingForm, _MutableMappingForm):
    """Mutable shape mapping: key-value ops + exists/extract + set/erase."""


class ReactiveMappingForm(ReactiveCollectionForm, MutableMappingForm, _ReactiveMappingForm):
    """Reactive shape mapping: adds on_change and the tree-aware on_child_change family."""


class OrderedMappingForm(MappingForm, _OrderedMappingForm):
    """Ordered shape mapping: reversed reads and paging over the mapping surface."""

    def _wrap_values_stream(self, operand: Nu) -> Iterator:
        """A stream over its values (``reversed_values``), typed by the declaration."""
        from collections.abc import Iterator as PyIterator

        from nu.forms import Iterator

        return holding(Iterator(operand), PyIterator, elem=self._declared.elem)

    def _wrap_keys_page(self, operand: Nu) -> List:
        """A page of keys: a List carrying the declared key type on."""
        from nu.forms import List

        return holding(List(operand), list, elem=self._declared.key)


class MutableOrderedMappingForm(MutableMappingForm, OrderedMappingForm, _MutableOrderedMappingForm):
    """Mutable ordered shape mapping: ordered reads + in-place writes + set/erase."""


class ReactiveOrderedMappingForm(
    ReactiveMappingForm, MutableOrderedMappingForm, _ReactiveOrderedMappingForm
):
    """Reactive ordered shape mapping: adds on_change and the tree-aware on_child_change family."""


class MappingRef(MappingForm, StructuredRef):
    """Key-value container Ref; ``ref[key]`` navigates to the value's child Ref.

    Navigation is defined once here and routes through ``_wrap_item_ref``, the
    one hook that returns a ref rather than a form. It is a substrate plug-point
    on ``StructuredRef``: the child is always a fabric's own ref, so the fabric's
    substrate base supplies it, and a fabric that leaves it out fails loudly.
    """

    def __getitem__(self, key: object) -> StructuredRef:
        """Navigate to the child Ref at ``key``, with self as parent."""
        return self._wrap_item_ref(key)


class MutableMappingRef(MutableMappingForm, MappingRef):
    """Mutable key-value container Ref.

    Adds: set(k,v), delete(k), update(), store(v), erase() on top of MappingRef.
    """


class ReactiveMappingRef(ReactiveMappingForm, MutableMappingRef):
    """Reactive key-value container Ref.

    Adds: on_change() (generic), on_child_change(), on_children_change(),
    on_descendants_change() (shape-domain) on top of MutableMappingRef.
    """


class OrderedMappingRef(OrderedMappingForm, MappingRef):
    """Ordered key-value container Ref.

    Adds: reversed_keys(), reversed_values(), reversed_items() and paged
    keys(after=, limit=) / reversed_keys(before=, limit=) on top of MappingRef.
    """


class MutableOrderedMappingRef(MutableOrderedMappingForm, OrderedMappingRef, MutableMappingRef):
    """Mutable ordered key-value container Ref.

    Adds: the in-place writes of MutableMappingRef on top of OrderedMappingRef.
    """


class ReactiveOrderedMappingRef(
    ReactiveOrderedMappingForm, MutableOrderedMappingRef, ReactiveMappingRef
):
    """Reactive ordered key-value container Ref.

    Adds: on_change(), on_child_change(), on_children_change(),
    on_descendants_change() on top of MutableOrderedMappingRef.
    """
