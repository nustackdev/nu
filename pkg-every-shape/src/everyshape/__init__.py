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

Types (concrete Python types — everyshape.types):
    ListBase -> ReactiveListBase          (mutable sequence)
    TupleBase -> ReactiveTupleBase        (immutable sequence)
    DictBase -> ReactiveDictBase          (mutable mapping)
    SetBase -> ReactiveSetBase            (mutable set)
    FrozenSetBase -> ReactiveFrozenSetBase (immutable set)

Refs (collection bases + Ref — everyshape.refs):
    Ref: Base for all document-model refs.
    ItemRef -> MutableItemRef -> ReactiveItemRef
    ShapeRef -> MutableShapeRef -> ReactiveShapeRef
    SequenceRefBase -> MutableSequenceRefBase -> ReactiveSequenceRefBase
    MappingRefBase -> MutableMappingRefBase -> ReactiveMappingRefBase
    ShapesListRefBase -> ReactiveShapesListRefBase
    ShapesDictRefBase -> ReactiveShapesDictRefBase
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
    ReactiveItemBase,
    ReactiveMappingBase,
    ReactiveSequenceBase,
    SequenceBase,
)
from everyshape.refs import (
    ItemRef,
    MappingRefBase,
    MutableItemRef,
    MutableMappingRefBase,
    MutableSequenceRefBase,
    MutableShapeRef,
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
from everyshape.types import (
    DictBase,
    FrozenSetBase,
    ListBase,
    ReactiveDictBase,
    ReactiveFrozenSetBase,
    ReactiveListBase,
    ReactiveSetBase,
    ReactiveTupleBase,
    SetBase,
    TupleBase,
)


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
    # Types (concrete Python types)
    "ListBase",
    "ReactiveListBase",
    "TupleBase",
    "ReactiveTupleBase",
    "DictBase",
    "ReactiveDictBase",
    "SetBase",
    "ReactiveSetBase",
    "FrozenSetBase",
    "ReactiveFrozenSetBase",
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
    "ReactiveShapesListRefBase",
    "ShapesDictRefBase",
    "ReactiveShapesDictRefBase",
    # Shape system
    "Shape",
    "ShapeMeta",
    "SlotDescriptor",
    "Slot",
]
