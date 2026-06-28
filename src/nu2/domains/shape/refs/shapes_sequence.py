"""ShapesSequenceRef hierarchy — sequence-of-shapes Ref + Form mixin tiers.

    ShapesSequenceRef         = shape.SequenceForm + _StructuredRef
    MutableShapesSequenceRef  = shape.MutableSequenceForm + ShapesSequenceRef
    ReactiveShapesSequenceRef = shape.ReactiveSequenceForm + MutableShapesSequenceRef

shape.SequenceForm already composes generic SequenceForm + shape CollectionForm,
so exists()/missing()/extract()/store()/erase() are all present without a
separate ItemForm in the MRO.

Subscript access (``ref[i]``) returns a matching-tier ShapeRef whose address
is the index. The element shape type is fixed at construction via
``item_shape_type``.

Form composition provides:
    base:     len(), contains(), iter(), [i], first_elem(), last_elem(), ...,
              exists(), missing(), extract()
    mutable:  + append(v), extend(), insert(i,v), pop(), ..., store(v), erase()
    reactive: + on_change() (generic), on_child_change(), on_children_change(),
                on_descendants_change() (shape-domain)

v1 reference: ``src/nu/shapes/refs/shapessequence.py``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu2.domains.shape.forms.sequence import MutableSequenceForm, ReactiveSequenceForm, SequenceForm

from .base import _StructuredRef
from .shape import MutableShapeRef, ReactiveShapeRef, ShapeRef


if TYPE_CHECKING:
    from nu2.domains.shape.dsl import Shape

__all__ = [
    "MutableShapesSequenceRef",
    "ReactiveShapesSequenceRef",
    "ShapesSequenceRef",
]


class ShapesSequenceRef(SequenceForm, _StructuredRef):
    """Sequence-of-shapes Ref; subscript descent returns a ShapeRef."""

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
        """Shape class for each element in this sequence."""
        return self._item_shape_type

    def __getitem__(self, index: object) -> ShapeRef:
        """Return a ShapeRef at index, with self as parent."""
        return ShapeRef(
            index,
            shape_type=self._item_shape_type,
            parent_ref=self,
            owner_shape=self._owner_shape,
        )


class MutableShapesSequenceRef(MutableSequenceForm, ShapesSequenceRef):
    """Mutable sequence-of-shapes Ref; subscript returns MutableShapeRef.

    Adds: append(v), extend(), insert(i,v), pop(), ..., store(v), erase().
    """

    def __getitem__(self, index: object) -> MutableShapeRef:
        """Return a MutableShapeRef at index, with self as parent."""
        return MutableShapeRef(
            index,
            shape_type=self._item_shape_type,
            parent_ref=self,
            owner_shape=self._owner_shape,
        )


class ReactiveShapesSequenceRef(ReactiveSequenceForm, MutableShapesSequenceRef):
    """Reactive sequence-of-shapes Ref; subscript returns ReactiveShapeRef.

    Adds: on_change(), on_child_change(), on_children_change(),
    on_descendants_change().
    """

    def __getitem__(self, index: object) -> ReactiveShapeRef:
        """Return a ReactiveShapeRef at index, with self as parent."""
        return ReactiveShapeRef(
            index,
            shape_type=self._item_shape_type,
            parent_ref=self,
            owner_shape=self._owner_shape,
        )
