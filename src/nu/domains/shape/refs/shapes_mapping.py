"""ShapesMappingRef hierarchy — mapping-of-shapes Ref + Form mixin tiers.

    ShapesMappingRef         = shape.MappingForm + StructuredRef
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

from .base import StructuredRef
from .shape import MutableShapeRef, ReactiveShapeRef, ShapeRef


if TYPE_CHECKING:
    from nu.domains.shape.dsl import Shape

__all__ = [
    "MutableShapesMappingRef",
    "ReactiveShapesMappingRef",
    "ShapesMappingRef",
]


class ShapesMappingRef[ItemResultT](MappingForm, StructuredRef):
    """Mapping-of-shapes Ref; subscript descent returns a ShapeRef.

    Navigation is defined ONCE (``__getitem__``) and routes through
    ``_wrap_item_ref``; each tier defaults to the matching-tier ShapeRef, and
    substrates override it (binding ``ItemResultT``) to return their own ShapeRef.
    """

    def __init__(
        self,
        address: object,
        *,
        item_shape_type: type[Shape],
        parent_ref: StructuredRef | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        super().__init__(address, parent_ref=parent_ref, owner_shape=owner_shape)
        self._payload["item_shape_type"] = item_shape_type

    def _wrap_item_ref(self, address: object) -> ItemResultT:
        """Build the child ShapeRef at ``address``, with self as parent."""
        return ShapeRef(  # type: ignore[return-value]
            address,
            shape_type=self._payload["item_shape_type"],
            parent_ref=self,
            owner_shape=self._owner_shape,
        )

    def __getitem__(self, key: object) -> ItemResultT:
        """Navigate to the child ShapeRef at ``key``, with self as parent."""
        return self._wrap_item_ref(key)


class MutableShapesMappingRef[ItemResultT](MutableMappingForm, ShapesMappingRef[ItemResultT]):
    """Mutable mapping-of-shapes Ref; subscript returns MutableShapeRef.

    Adds: set(k,v), delete(k), update(), ..., store(v), erase().
    """

    def _wrap_item_ref(self, address: object) -> ItemResultT:
        return MutableShapeRef(  # type: ignore[return-value]
            address,
            shape_type=self._payload["item_shape_type"],
            parent_ref=self,
            owner_shape=self._owner_shape,
        )


class ReactiveShapesMappingRef[ItemResultT](ReactiveMappingForm, MutableShapesMappingRef[ItemResultT]):
    """Reactive mapping-of-shapes Ref; subscript returns ReactiveShapeRef.

    Adds: on_change(), on_child_change(), on_children_change(),
    on_descendants_change().
    """

    def _wrap_item_ref(self, address: object) -> ItemResultT:
        return ReactiveShapeRef(  # type: ignore[return-value]
            address,
            shape_type=self._payload["item_shape_type"],
            parent_ref=self,
            owner_shape=self._owner_shape,
        )
