"""Mapping family: a key-value collection in a shape fabric.

Forms weave the Python mapping surface with the shape collection ops, tier by
tier, and type every result by what the slot declared: a value reads as the
declared value's form, and keys, values, items and whole-mapping results carry
the declared types on.

Refs add descent. ``ref[key]`` is the child ref at that key, built by the
fabric from the declared value, because only the fabric knows which of its
refs holds that value.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.forms.collections.abc.mapping import MappingForm as _MappingForm
from nu.forms.collections.abc.mapping import MutableMappingForm as _MutableMappingForm
from nu.forms.collections.abc.mapping import ReactiveMappingForm as _ReactiveMappingForm

from .base import StructuredRef
from .collection import (
    CollectionForm,
    MutableCollectionForm,
    ReactiveCollectionForm,
    form_of,
    holding,
)


if TYPE_CHECKING:
    from nu.forms import Dict, DictItems, DictKeys, DictValues, Iterator
    from nu.lang import Form, Nu


__all__ = [
    "MappingForm",
    "MappingRef",
    "MutableMappingForm",
    "MutableMappingRef",
    "ReactiveMappingForm",
    "ReactiveMappingRef",
]


class MappingForm(_MappingForm, CollectionForm):
    """Shape mapping: key-value ops + exists/missing/extract, typed by the declaration."""

    def _wrap_value_result(self, operand: Nu) -> Form:
        return form_of(self._declared.elem)(operand)  # type: ignore[return-value]

    def _wrap_element_result(self, operand: Nu) -> Form:
        return form_of(self._declared.key)(operand)  # type: ignore[return-value]

    def iter(self) -> Iterator:
        """A lazy stream over its keys, typed by the declared key."""
        from nu.core import Iter

        return self._wrap_iterable_result(Iter(self))

    def _wrap_iterable_result(self, operand: Nu) -> Iterator:
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

    def _wrap_mapping_result(self, operand: Nu) -> Dict:
        from nu.forms import Dict

        declared = self._declared
        return holding(Dict(operand), dict, key=declared.key, elem=declared.elem)


class MutableMappingForm(_MutableMappingForm, MutableCollectionForm):
    """Mutable shape mapping: key-value ops + exists/missing/extract + set/erase."""


class ReactiveMappingForm(_ReactiveMappingForm, MutableMappingForm, ReactiveCollectionForm):
    """Reactive shape mapping. Adds on_change + tree-aware on_child_change* family.

    MRO provides:
        on_change()               from generic ReactiveMappingForm
        on_child_change(addr)     from shape ReactiveCollectionForm
        on_children_change()      from shape ReactiveCollectionForm
        on_descendants_change(*)  from shape ReactiveCollectionForm
    """


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
