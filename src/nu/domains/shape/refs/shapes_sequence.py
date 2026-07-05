"""ShapesSequenceRef hierarchy — sequence-of-shapes Ref + Form mixin tiers.

    ShapesSequenceRef         = shape.SequenceForm + StructuredRef
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
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.domains.shape.forms.sequence import MutableSequenceForm, ReactiveSequenceForm, SequenceForm

from .base import StructuredRef
from .shape import MutableShapeRef, ReactiveShapeRef, ShapeRef


if TYPE_CHECKING:
    from nu.domains.shape.dsl import Shape

__all__ = [
    "MutableShapesSequenceRef",
    "ReactiveShapesSequenceRef",
    "ShapesSequenceRef",
]


class ShapesSequenceRef[ItemResultT](SequenceForm, StructuredRef):
    """Sequence-of-shapes Ref; subscript descent returns a ShapeRef.

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

    def __getitem__(self, index: object) -> ItemResultT:
        """Navigate to the child ShapeRef at ``index``, with self as parent."""
        return self._wrap_item_ref(index)


class MutableShapesSequenceRef[ItemResultT](MutableSequenceForm, ShapesSequenceRef[ItemResultT]):
    """Mutable sequence-of-shapes Ref; subscript returns MutableShapeRef.

    Adds: append(v), extend(), insert(i,v), pop(), ..., store(v), erase().
    """

    def _wrap_item_ref(self, address: object) -> ItemResultT:
        return MutableShapeRef(  # type: ignore[return-value]
            address,
            shape_type=self._payload["item_shape_type"],
            parent_ref=self,
            owner_shape=self._owner_shape,
        )


class ReactiveShapesSequenceRef[ItemResultT](ReactiveSequenceForm, MutableShapesSequenceRef[ItemResultT]):
    """Reactive sequence-of-shapes Ref; subscript returns ReactiveShapeRef.

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
