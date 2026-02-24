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
    SetLikeBase -> MutableSetBase -> ReactiveSetBase

Types (concrete Python types — everyshape.types):
    ListType -> ReactiveListType      (mutable sequence)
    TupleType                         (immutable sequence)
    DictType -> ReactiveDictType      (mutable mapping)
    SetType -> ReactiveSetType        (mutable set)
    FrozenSetType                     (immutable set)

Refs (collection bases + Ref — everyshape.refs):
    Ref: Base for all document-model refs.
    ItemRef -> MutableItemRef -> ReactiveItemRef
    ShapeRef -> MutableShapeRef -> ReactiveShapeRef
    SequenceRefBase -> MutableSequenceRefBase -> ReactiveSequenceRefBase
    MappingRefBase -> MutableMappingRefBase -> ReactiveMappingRefBase
    SetLikeRefBase -> MutableSetRefBase -> ReactiveSetRefBase
    ShapesSequenceRefBase -> MutableShapesSequenceRefBase -> ReactiveShapesSequenceRefBase
    ShapesMappingRefBase -> MutableShapesMappingRefBase -> ReactiveShapesMappingRefBase
"""

from everyshape.capabilities import (
    CollectionDeletableBase,
    CollectionExistableBase,
    CollectionGettableBase,
    CollectionSettableBase,
    ItemDeletableBase,
    ItemExistableBase,
    ItemGettableBase,
    ItemSettableBase,
    PrimitiveObservableBase,
    ViewObservableBase,
)
from everyshape.collections import (
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
from everyshape.flows import React, ReactForever, ReactWhile
from everyshape.morphisms import (
    ChangeOp,
    CollectionDeleteCmd,
    CollectionExistsOp,
    CollectionGetOp,
    CollectionMissingOp,
    CollectionSetCmd,
    ItemDeleteCmd,
    ItemExistsOp,
    ItemGetOp,
    ItemMissingOp,
    ItemSetCmd,
    OnChangeOp,
    OnChildChangeOp,
    OnChildrenChangeOp,
    OnDescendantsChangeOp,
    OnPrimitiveChangeOp,
)
from everyshape.protocols import (
    ChildObservableProtocol,
    ChildrenObservableProtocol,
    DescendantsObservableProtocol,
    ObservableProtocol,
)
from everyshape.refs import (
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
from everyshape.shape import Shape, ShapeMeta, Slot, SlotDescriptor
from everyshape.types import (
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
    "CollectionDeletableBase",
    "CollectionExistableBase",
    "CollectionGettableBase",
    "CollectionSettableBase",
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
    # Morphisms — Item
    "ItemGetOp",
    "ItemSetCmd",
    "ItemDeleteCmd",
    "ItemExistsOp",
    "ItemMissingOp",
    # Morphisms — Collection
    "CollectionGetOp",
    "CollectionSetCmd",
    "CollectionDeleteCmd",
    "CollectionExistsOp",
    "CollectionMissingOp",
    # Morphisms — Reactive
    "ChangeOp",
    "OnChangeOp",
    "OnPrimitiveChangeOp",
    "OnChildChangeOp",
    "OnChildrenChangeOp",
    "OnDescendantsChangeOp",
]
