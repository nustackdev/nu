"""everyshape - Declarative document model for everybase.

Provides the shape metaclass system for defining hierarchical
document structures with typed slots, plus abstract ref hierarchies
for items and collections in the document model.

Shape System:
    Shape: Base class for declarative shape definitions.
    ShapeMeta: Metaclass that processes slot definitions at class creation time.
    SlotDescriptor: Descriptor bridging slot definitions to refs at runtime.
    Slot: Universal slot that creates any Ref type.

Ref Hierarchy:
    Ref: Base for all document-model refs (address/parent/shape).

Item Refs (typed values):
    ItemRef -> MutableItemRef -> ReactiveItemRef

Collection Refs (containers):
    ShapeRef -> MutableShapeRef -> ReactiveShapeRef
    MappingRef -> MutableMappingRef -> ReactiveMappingRef
    SequenceRef -> MutableSequenceRef -> ReactiveSequenceRef
    ShapesListRef -> MutableShapesListRef -> ReactiveShapesListRef
    ShapesDictRef -> MutableShapesDictRef -> ReactiveShapesDictRef
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
from everyshape.shape import Shape, ShapeMeta, SlotDescriptor
from everyshape.shape_ref import Ref
from everyshape.slot import Slot


__all__ = [
    "ItemRef",
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
    "Ref",
    "SequenceRef",
    "Shape",
    "ShapeMeta",
    "ShapeRef",
    "ShapesDictRef",
    "ShapesListRef",
    "Slot",
    "SlotDescriptor",
]
