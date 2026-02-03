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

Shape Refs (structured containers):
    ShapeRef -> MutableShapeRef -> ReactiveShapeRef

Collection RefBases (containers — substrates inherit these):
    SequenceRefBase -> MutableSequenceRefBase -> ReactiveSequenceRefBase
    MappingRefBase -> MutableMappingRefBase -> ReactiveMappingRefBase
    ShapesListRefBase -> MutableShapesListRefBase -> ReactiveShapesListRefBase
    ShapesDictRefBase -> MutableShapesDictRefBase -> ReactiveShapesDictRefBase
"""

from everyshape.capabilities import (
    CollectionClearableBase,
    CollectionExistableBase,
    CollectionExtractableBase,
    CollectionLengthableBase,
    CollectionStorableBase,
    ItemDeletableBase,
    ItemExistableBase,
    ItemGettableBase,
    ItemSettableBase,
    LocationDeletableProtocol,
    LocationExistableProtocol,
    LocationGettableProtocol,
    LocationObservableProtocol,
    LocationSettableProtocol,
    PrimitiveObservableBase,
    ViewObservableBase,
)
from everyshape.collections import (
    ItemRef,
    MappingRefBase,
    MutableItemRef,
    MutableMappingRefBase,
    MutableSequenceRefBase,
    MutableShapesDictRefBase,
    MutableShapesListRefBase,
    ReactiveItemRef,
    ReactiveMappingRefBase,
    ReactiveSequenceRefBase,
    ReactiveShapesDictRefBase,
    ReactiveShapesListRefBase,
    SequenceRefBase,
    ShapesDictRefBase,
    ShapesListRefBase,
)
from everyshape.ref import Ref
from everyshape.ref_structured import MutableShapeRef, ReactiveShapeRef, ShapeRef
from everyshape.shape import Shape, ShapeMeta, SlotDescriptor
from everyshape.slot import Slot


__all__ = [  # noqa: RUF022
    # Capabilities — Location protocols
    "LocationDeletableProtocol",
    "LocationExistableProtocol",
    "LocationGettableProtocol",
    "LocationObservableProtocol",
    "LocationSettableProtocol",
    # Capabilities — Item bases
    "ItemDeletableBase",
    "ItemExistableBase",
    "ItemGettableBase",
    "ItemSettableBase",
    # Capabilities — Collection bases
    "CollectionClearableBase",
    "CollectionExistableBase",
    "CollectionExtractableBase",
    "CollectionLengthableBase",
    "CollectionStorableBase",
    # Capabilities — Reactive bases
    "PrimitiveObservableBase",
    "ViewObservableBase",
    # Ref base
    "Ref",
    # Item refs
    "ItemRef",
    "MutableItemRef",
    "ReactiveItemRef",
    # Shape refs
    "ShapeRef",
    "MutableShapeRef",
    "ReactiveShapeRef",
    # Collection RefBases
    "MappingRefBase",
    "MutableMappingRefBase",
    "ReactiveMappingRefBase",
    "SequenceRefBase",
    "MutableSequenceRefBase",
    "ReactiveSequenceRefBase",
    "ShapesListRefBase",
    "MutableShapesListRefBase",
    "ReactiveShapesListRefBase",
    "ShapesDictRefBase",
    "MutableShapesDictRefBase",
    "ReactiveShapesDictRefBase",
    # Shape system
    "Shape",
    "ShapeMeta",
    "SlotDescriptor",
    "Slot",
]
