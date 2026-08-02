"""Shape-fabric Ref blueprints: 3-tier matrix.

Re-exports all 21 Ref blueprints (7 families x 3 tiers) and the private
abstract base ``StructuredRef`` for substrate authors who extend it directly.

Families:
    Item          : leaf typed value
    Mapping       : key-value container
    Sequence      : ordered element container
    Set           : unordered unique-element container
    Shape         : structured named-slot container
    ShapesMapping : mapping whose values are shapes
    ShapesSequence: sequence whose elements are shapes

Tiers per family:
    Base      : read + exists/missing
    Mutable   : + write/erase + collection mutations
    Reactive  : + on_change family
"""

from __future__ import annotations

from .base import StructuredRef as StructuredRef  # re-export for substrate authors
from .item import ItemRef, MutableItemRef, ReactiveItemRef
from .mapping import MappingRef, MutableMappingRef, ReactiveMappingRef
from .sequence import MutableSequenceRef, ReactiveSequenceRef, SequenceRef
from .set_ import MutableSetRef, ReactiveSetRef, SetRef
from .shape import MutableShapeRef, ReactiveShapeRef, ShapeRef
from .shapes_mapping import MutableShapesMappingRef, ReactiveShapesMappingRef, ShapesMappingRef
from .shapes_sequence import (
    MutableShapesSequenceRef,
    ReactiveShapesSequenceRef,
    ShapesSequenceRef,
)


__all__ = [
    # Item
    "ItemRef",
    # Mapping
    "MappingRef",
    "MutableItemRef",
    "MutableMappingRef",
    # Sequence
    "MutableSequenceRef",
    # Set
    "MutableSetRef",
    # Shape
    "MutableShapeRef",
    # ShapesMapping
    "MutableShapesMappingRef",
    # ShapesSequence
    "MutableShapesSequenceRef",
    "ReactiveItemRef",
    "ReactiveMappingRef",
    "ReactiveSequenceRef",
    "ReactiveSetRef",
    "ReactiveShapeRef",
    "ReactiveShapesMappingRef",
    "ReactiveShapesSequenceRef",
    "SequenceRef",
    "SetRef",
    "ShapeRef",
    "ShapesMappingRef",
    "ShapesSequenceRef",
]
