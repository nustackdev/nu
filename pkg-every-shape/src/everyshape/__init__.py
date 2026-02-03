"""everyshape - Declarative document model for everybase.

Provides the shape metaclass system for defining hierarchical
document structures with typed slots, plus abstract ref hierarchies
for items and collections in the document model.

Shape System:
    Shape: Base class for declarative shape definitions.
    ShapeMeta: Metaclass that processes slot definitions at class creation time.
    SlotDescriptor: Descriptor bridging slot definitions to refs at runtime.
    Slot: Universal slot that creates any Ref type.

Collection Bases (pure, no Ref — everyshape.collections):
    ItemBase -> MutableItemBase -> ReactiveItemBase
    SequenceBase -> MutableSequenceBase -> ReactiveSequenceBase
    MappingBase -> MutableMappingBase -> ReactiveMappingBase
    ShapesListBase -> MutableShapesListBase -> ReactiveShapesListBase
    ShapesDictBase -> MutableShapesDictBase -> ReactiveShapesDictBase

Refs (collection bases + Ref — everyshape.refs):
    Ref: Base for all document-model refs.
    ItemRef -> MutableItemRef -> ReactiveItemRef
    ShapeRef -> MutableShapeRef -> ReactiveShapeRef
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
    ItemBase,
    MappingBase,
    MutableItemBase,
    MutableMappingBase,
    MutableSequenceBase,
    MutableShapesDictBase,
    MutableShapesListBase,
    ReactiveItemBase,
    ReactiveMappingBase,
    ReactiveSequenceBase,
    ReactiveShapesDictBase,
    ReactiveShapesListBase,
    SequenceBase,
    ShapesDictBase,
    ShapesListBase,
)
from everyshape.refs import (
    ItemRef,
    MappingRefBase,
    MutableItemRef,
    MutableMappingRefBase,
    MutableSequenceRefBase,
    MutableShapeRef,
    MutableShapesDictRefBase,
    MutableShapesListRefBase,
    ReactiveItemRef,
    ReactiveMappingRefBase,
    ReactiveSequenceRefBase,
    ReactiveShapeRef,
    ReactiveShapesDictRefBase,
    ReactiveShapesListRefBase,
    Ref,
    SequenceRefBase,
    ShapeRef,
    ShapesDictRefBase,
    ShapesListRefBase,
)
from everyshape.shape import Shape, ShapeMeta, Slot, SlotDescriptor


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
    # Collection bases (pure)
    "ItemBase",
    "MutableItemBase",
    "ReactiveItemBase",
    "SequenceBase",
    "MutableSequenceBase",
    "ReactiveSequenceBase",
    "MappingBase",
    "MutableMappingBase",
    "ReactiveMappingBase",
    "ShapesListBase",
    "MutableShapesListBase",
    "ReactiveShapesListBase",
    "ShapesDictBase",
    "MutableShapesDictBase",
    "ReactiveShapesDictBase",
    # Refs
    "ItemRef",
    "MutableItemRef",
    "ReactiveItemRef",
    "ShapeRef",
    "MutableShapeRef",
    "ReactiveShapeRef",
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
