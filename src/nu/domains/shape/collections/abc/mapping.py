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

from nu.forms.collections.abc.mapping import MappingSurface as _MappingSurface
from nu.forms.collections.abc.mapping import MutableMappingSurface as _MutableMappingSurface
from nu.forms.collections.abc.mapping import (
    MutableOrderedMappingSurface as _MutableOrderedMappingSurface,
)
from nu.forms.collections.abc.mapping import OrderedMappingSurface as _OrderedMappingSurface
from nu.forms.collections.abc.mapping import ReactiveMappingSurface as _ReactiveMappingSurface
from nu.forms.collections.abc.mapping import (
    ReactiveOrderedMappingSurface as _ReactiveOrderedMappingSurface,
)

from ...base import StructuredRef
from ...collection import (
    CollectionSurface,
    MutableCollectionSurface,
    ReactiveCollectionSurface,
    form_of,
    holds,
)


if TYPE_CHECKING:
    from nu.forms import DictItems, DictKeys, DictValues, Iterator, List
    from nu.forms.primitives import Object
    from nu.lang import Nu


__all__ = [
    "MappingRef",
    "MappingSurface",
    "MutableMappingRef",
    "MutableMappingSurface",
    "MutableOrderedMappingRef",
    "MutableOrderedMappingSurface",
    "OrderedMappingRef",
    "OrderedMappingSurface",
    "ReactiveMappingRef",
    "ReactiveMappingSurface",
    "ReactiveOrderedMappingRef",
    "ReactiveOrderedMappingSurface",
]


class MappingSurface(CollectionSurface, _MappingSurface):
    """Shape mapping: key-value ops + exists/extract, typed by the declaration."""

    def _wrap_value_result(self, operand: Nu) -> Object:
        return form_of(self._declared.elem)(operand)  # type: ignore[return-value]

    def _wrap_element_result(self, operand: Nu) -> Object:
        return form_of(self._declared.key)(operand)  # type: ignore[return-value]

    def _wrap_iterable_result(self, operand: Nu) -> Iterator:
        """A stream over its keys (``iter``), typed by the declaration."""
        from collections.abc import Iterator as PyIterator

        from nu.forms import Iterator

        return Iterator(operand, type_info=holds(PyIterator, elem=self._declared.key))

    def _wrap_keys_result(self, operand: Nu) -> DictKeys:
        from nu.forms import DictKeys

        return DictKeys(operand, type_info=holds(set, elem=self._declared.key))

    def _wrap_values_result(self, operand: Nu) -> DictValues:
        from nu.forms import DictValues

        return DictValues(operand, type_info=holds(list, elem=self._declared.elem))

    def _wrap_items_result(self, operand: Nu) -> DictItems:
        from nu.forms import DictItems

        declared = self._declared
        return DictItems(operand, type_info=holds(dict, key=declared.key, elem=declared.elem))


class MutableMappingSurface(MutableCollectionSurface, MappingSurface, _MutableMappingSurface):
    """Mutable shape mapping: key-value ops + exists/extract + set/erase."""


class ReactiveMappingSurface(
    ReactiveCollectionSurface, MutableMappingSurface, _ReactiveMappingSurface
):
    """Reactive shape mapping: adds on_change and the tree-aware on_child_change family."""


class OrderedMappingSurface(MappingSurface, _OrderedMappingSurface):
    """Ordered shape mapping: reversed reads and paging over the mapping surface."""

    def _wrap_values_stream(self, operand: Nu) -> Iterator:
        """A stream over its values (``reversed_values``), typed by the declaration."""
        from collections.abc import Iterator as PyIterator

        from nu.forms import Iterator

        return Iterator(operand, type_info=holds(PyIterator, elem=self._declared.elem))

    def _wrap_keys_page(self, operand: Nu) -> List:
        """A page of keys: a List carrying the declared key type on."""
        from nu.forms import List

        return List(operand, type_info=holds(list, elem=self._declared.key))


class MutableOrderedMappingSurface(
    MutableMappingSurface, OrderedMappingSurface, _MutableOrderedMappingSurface
):
    """Mutable ordered shape mapping: ordered reads + in-place writes + set/erase."""


class ReactiveOrderedMappingSurface(
    ReactiveMappingSurface, MutableOrderedMappingSurface, _ReactiveOrderedMappingSurface
):
    """Reactive ordered shape mapping: adds on_change and the tree-aware on_child_change family."""


class MappingRef(MappingSurface, StructuredRef):
    """Key-value container Ref; ``ref[key]`` navigates to the value's child Ref.

    Navigation is defined once here and routes through ``_wrap_item_ref``, the
    one hook that returns a ref rather than a form. It is a substrate plug-point
    on ``StructuredRef``: the child is always a fabric's own ref, so the fabric's
    substrate base supplies it, and a fabric that leaves it out fails loudly.
    """

    def __getitem__(self, key: object) -> StructuredRef:
        """Navigate to the child Ref at ``key``, with self as parent."""
        return self._wrap_item_ref(key)


class MutableMappingRef(MutableMappingSurface, MappingRef):
    """Mutable key-value container Ref.

    Adds: set(k,v), delete(k), update(), store(v), erase() on top of MappingRef.
    """


class ReactiveMappingRef(ReactiveMappingSurface, MutableMappingRef):
    """Reactive key-value container Ref.

    Adds: on_change() (generic), on_child_change(), on_children_change(),
    on_descendants_change() (shape-domain) on top of MutableMappingRef.
    """


class OrderedMappingRef(OrderedMappingSurface, MappingRef):
    """Ordered key-value container Ref.

    Adds: reversed_keys(), reversed_values(), reversed_items() and paged
    keys(after=, limit=) / reversed_keys(before=, limit=) on top of MappingRef.
    """


class MutableOrderedMappingRef(MutableOrderedMappingSurface, OrderedMappingRef, MutableMappingRef):
    """Mutable ordered key-value container Ref.

    Adds: the in-place writes of MutableMappingRef on top of OrderedMappingRef.
    """


class ReactiveOrderedMappingRef(
    ReactiveOrderedMappingSurface, MutableOrderedMappingRef, ReactiveMappingRef
):
    """Reactive ordered key-value container Ref.

    Adds: on_change(), on_child_change(), on_children_change(),
    on_descendants_change() on top of MutableOrderedMappingRef.
    """
