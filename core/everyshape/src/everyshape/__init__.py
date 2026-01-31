"""everyshape - Declarative document model for everybase.

Provides the shape metaclass system for defining hierarchical
document structures with typed slots, plus abstract ref hierarchies
for items and collections in the document model.

Shape System:
    ShapeMeta: Metaclass that processes slot definitions at class creation time.
    ShapeBase: Base class for declarative shape definitions.
    SlotDescriptor: Descriptor bridging slot definitions to refs at runtime.

Item Refs (typed values):
    ItemRef → MutableItemRef → ReactiveItemRef

Collection Refs (containers):
    ShapeRef → MutableShapeRef → ReactiveShapeRef
    MappingRef → MutableMappingRef → ReactiveMappingRef
    SequenceRef → MutableSequenceRef → ReactiveSequenceRef
    ShapesListRef → MutableShapesListRef → ReactiveShapesListRef
    ShapesDictRef → MutableShapesDictRef → ReactiveShapesDictRef
"""

from everyshape.collections import (
    MappingRef,
    MutableMappingRef,
    MutableSequenceRef,
    MutableShapeRef,
    MutableShapesDictRef,
    MutableShapesListRef,
    ReactiveMappingRef,
    ReactiveSequenceRef,
    ReactiveShapeRef,
    ReactiveShapesDictRef,
    ReactiveShapesListRef,
    SequenceRef,
    ShapeRef,
    ShapesDictRef,
    ShapesListRef,
)
from everyshape.items import ItemRef, MutableItemRef, ReactiveItemRef
from everyshape.shape import ShapeBase, ShapeMeta, SlotDescriptor


__all__ = [
    # Items
    "ItemRef",
    # Mappings
    "MappingRef",
    "MutableItemRef",
    "MutableMappingRef",
    "MutableSequenceRef",
    "MutableShapeRef",
    "MutableShapesDictRef",
    "MutableShapesListRef",
    "ReactiveItemRef",
    "ReactiveMappingRef",
    "ReactiveSequenceRef",
    "ReactiveShapeRef",
    "ReactiveShapesDictRef",
    "ReactiveShapesListRef",
    # Sequences
    "SequenceRef",
    # Shape system
    "ShapeBase",
    "ShapeMeta",
    # Shapes
    "ShapeRef",
    "ShapesDictRef",
    # Shapes in collections
    "ShapesListRef",
    "SlotDescriptor",
]
