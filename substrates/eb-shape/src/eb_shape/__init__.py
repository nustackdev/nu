"""eb_shape - Declarative document model for everybase.

Provides the shape metaclass system for defining hierarchical
document structures with typed slots, plus abstract ref hierarchies
for items and collections in the document model.

Shape System:
    Shape: Base class for declarative shape definitions.
    ShapeMeta: Metaclass that processes slot definitions at class creation time.
    SlotDescriptor: Descriptor bridging slot definitions to refs at runtime.
    Slot: Universal slot that creates any Ref type.

Collection Bases (pure, no Ref — eb_shape.collections):
    ItemBase -> MutableItemBase -> ReactiveItemBase
    SequenceBase -> MutableSequenceBase -> ReactiveSequenceBase
    MappingBase -> MutableMappingBase -> ReactiveMappingBase
    SetLikeBase -> MutableSetBase -> ReactiveSetBase

Types (concrete Python types — eb_shape.types):
    ListType -> ReactiveListType      (mutable sequence)
    TupleType                         (immutable sequence)
    DictType -> ReactiveDictType      (mutable mapping)
    SetType -> ReactiveSetType        (mutable set)
    FrozenSetType                     (immutable set)

Refs (collection bases + Ref — eb_shape.refs):
    Ref: Base for all document-model refs.
    ItemRef -> MutableItemRef -> ReactiveItemRef
    ShapeRef -> MutableShapeRef -> ReactiveShapeRef
    SequenceRefBase -> MutableSequenceRefBase -> ReactiveSequenceRefBase
    MappingRefBase -> MutableMappingRefBase -> ReactiveMappingRefBase
    SetLikeRefBase -> MutableSetRefBase -> ReactiveSetRefBase
    ShapesSequenceRefBase -> MutableShapesSequenceRefBase -> ReactiveShapesSequenceRefBase
    ShapesMappingRefBase -> MutableShapesMappingRefBase -> ReactiveShapesMappingRefBase
"""

from eb_shape.capabilities import (
    CollectionClearableBase,
    CollectionExistableBase,
    CollectionExtractableBase,
    CollectionStorableBase,
    ItemDeletableBase,
    ItemExistableBase,
    ItemGettableBase,
    ItemSettableBase,
    PrimitiveObservableBase,
    ViewObservableBase,
)
from eb_shape.collections import (
    ItemBase,
    MappingBase,
    MutableItemBase,
    MutableMappingBase,
    MutableSequenceBase,
    MutableSetBase,
    ReactiveItemBase,
    ReactiveMappingBase,
    ReactiveSequenceBase,
    SequenceBase,
    SetLikeBase,
)
from eb_shape.flows import React, ReactForever, ReactWhile
from eb_shape.protocols import (
    ChildObservableProtocol,
    ChildrenObservableProtocol,
    ClearableProtocol,
    DescendantsObservableProtocol,
    ExtractableProtocol,
    ObservableProtocol,
    StorableProtocol,
)
from eb_shape.refs import (
    ItemRef,
    MappingRefBase,
    MutableItemRef,
    MutableMappingRefBase,
    MutableSequenceRefBase,
    MutableSetRefBase,
    MutableShapeRef,
    MutableShapesMappingRefBase,
    MutableShapesSequenceRefBase,
    ReactiveItemRef,
    ReactiveMappingRefBase,
    ReactiveSequenceRefBase,
    ReactiveSetRefBase,
    ReactiveShapeRef,
    ReactiveShapesMappingRefBase,
    ReactiveShapesSequenceRefBase,
    Ref,
    SequenceRefBase,
    SetLikeRefBase,
    ShapeRef,
    ShapesMappingRefBase,
    ShapesSequenceRefBase,
)
from eb_shape.shape import Shape, ShapeMeta, Slot, SlotDescriptor
from eb_shape.types import (
    DictType,
    FrozenSetType,
    ListType,
    ReactiveDictType,
    ReactiveListType,
    ReactiveSetType,
    SetType,
    TupleType,
)


__all__ = [  # noqa: RUF022
    # Protocols — Collection view
    "ClearableProtocol",
    "ExtractableProtocol",
    "StorableProtocol",
    # Protocols — Reactive view
    "ChildObservableProtocol",
    "ChildrenObservableProtocol",
    "DescendantsObservableProtocol",
    "ObservableProtocol",
    # Capabilities — Item bases
    "ItemDeletableBase",
    "ItemExistableBase",
    "ItemGettableBase",
    "ItemSettableBase",
    # Capabilities — Collection bases
    "CollectionClearableBase",
    "CollectionExistableBase",
    "CollectionExtractableBase",
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
    "SetLikeBase",
    "MutableSetBase",
    # Types (concrete Python types)
    "ListType",
    "ReactiveListType",
    "TupleType",
    "DictType",
    "ReactiveDictType",
    "SetType",
    "ReactiveSetType",
    "FrozenSetType",
    # Refs — Item
    "ItemRef",
    "MutableItemRef",
    "ReactiveItemRef",
    # Refs — Shape
    "ShapeRef",
    "MutableShapeRef",
    "ReactiveShapeRef",
    # Refs — Sequence
    "SequenceRefBase",
    "MutableSequenceRefBase",
    "ReactiveSequenceRefBase",
    # Refs — Mapping
    "MappingRefBase",
    "MutableMappingRefBase",
    "ReactiveMappingRefBase",
    # Refs — Set
    "SetLikeRefBase",
    "MutableSetRefBase",
    "ReactiveSetRefBase",
    # Refs — ShapesSequence
    "ShapesSequenceRefBase",
    "MutableShapesSequenceRefBase",
    "ReactiveShapesSequenceRefBase",
    # Refs — ShapesMapping
    "ShapesMappingRefBase",
    "MutableShapesMappingRefBase",
    "ReactiveShapesMappingRefBase",
    # Shape system
    "Shape",
    "ShapeMeta",
    "SlotDescriptor",
    "Slot",
    # Reactive flows
    "React",
    "ReactForever",
    "ReactWhile",
]
