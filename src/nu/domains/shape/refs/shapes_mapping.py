"""ShapesMappingRef hierarchy — mapping-of-shapes Ref + Form mixin tiers.

    ShapesMappingRef         = shape.MappingForm + _StructuredRef
    MutableShapesMappingRef  = shape.MutableMappingForm + ShapesMappingRef
    ReactiveShapesMappingRef = shape.ReactiveMappingForm + MutableShapesMappingRef

shape.MappingForm already composes generic MappingForm + shape CollectionForm,
so exists()/missing()/extract()/store()/erase() are all present without a
separate ItemForm in the MRO.

Subscript access (``ref[key]``) returns a matching-tier ShapeRef whose address
is the key. The shape type for items is fixed at construction via
``item_shape_type``.

Form composition provides:
    base:     len(), contains(), iter(), [k], keys(), values(), items(), ...,
              exists(), missing(), extract()
    mutable:  + set(k,v), delete(k), update(), ..., store(v), erase()
    reactive: + on_change() (generic), on_child_change(), on_children_change(),
                on_descendants_change() (shape-domain)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.domains.shape.forms.mapping import MappingForm, MutableMappingForm, ReactiveMappingForm

from .base import _StructuredRef
from .shape import MutableShapeRef, ReactiveShapeRef, ShapeRef


if TYPE_CHECKING:
    from nu.domains.shape.dsl import Shape

__all__ = [
    "MutableShapesMappingRef",
    "ReactiveShapesMappingRef",
    "ShapesMappingRef",
]


class ShapesMappingRef(MappingForm, _StructuredRef):
    """Mapping-of-shapes Ref; subscript descent returns a ShapeRef."""

    def __init__(
        self,
        address: object,
        *,
        item_shape_type: type[Shape],
        parent_ref: _StructuredRef | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(address, parent_ref=parent_ref, owner_shape=owner_shape)
        self._item_shape_type = item_shape_type

    @property
    def item_shape_type(self) -> type[Shape]:
        """Shape class for each value in this mapping."""
        return self._item_shape_type

    def __getitem__(self, key: object) -> ShapeRef:
        """Return a ShapeRef at key, with self as parent."""
        return ShapeRef(
            key,
            shape_type=self._item_shape_type,
            parent_ref=self,
            owner_shape=self._owner_shape,
        )


class MutableShapesMappingRef(MutableMappingForm, ShapesMappingRef):
    """Mutable mapping-of-shapes Ref; subscript returns MutableShapeRef.

    Adds: set(k,v), delete(k), update(), ..., store(v), erase().
    """

    def __getitem__(self, key: object) -> MutableShapeRef:
        """Return a MutableShapeRef at key, with self as parent."""
        return MutableShapeRef(
            key,
            shape_type=self._item_shape_type,
            parent_ref=self,
            owner_shape=self._owner_shape,
        )


class ReactiveShapesMappingRef(ReactiveMappingForm, MutableShapesMappingRef):
    """Reactive mapping-of-shapes Ref; subscript returns ReactiveShapeRef.

    Adds: on_change(), on_child_change(), on_children_change(),
    on_descendants_change().
    """

    def __getitem__(self, key: object) -> ReactiveShapeRef:
        """Return a ReactiveShapeRef at key, with self as parent."""
        return ReactiveShapeRef(
            key,
            shape_type=self._item_shape_type,
            parent_ref=self,
            owner_shape=self._owner_shape,
        )
