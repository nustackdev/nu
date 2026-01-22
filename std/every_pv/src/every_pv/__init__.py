"""every_pv - PV refs for everybase term system.

This package provides PV (polymorphic views) based ref implementations
for the everybase term system.

Package Structure:
    morphisms/    - PV-specific operations and commands
    protocols/    - PV capability protocols
    traits/       - Storage access traits and ref bases
    pv/           - Concrete PV ref implementations
    slots/        - Slot definitions for Shape system
    ref.py        - Abstract ref classes (PrimitiveRef, ViewRef)
    context.py    - KVContext for execution

Key Classes:
    Concrete PV Refs (from pv/):
        - PVIntRef, PVStrRef, PVFloatRef, PVBoolRef, PVBytesRef
        - PVItemRef, PVListItemRef, PVDictItemRef
        - PVDictRef, PVListRef
        - PVShapeRef, PVShapesListRef, PVShapesDictRef

    Slots (from slots/):
        - IntSlot, StrSlot, FloatSlot, BoolSlot, BytesSlot
        - ItemSlot, DictSlot, ListSlot
        - ShapeSlot, ShapesListSlot, ShapesDictSlot

    Context:
        - KVContext, SingularContext

Usage:
    from every_pv import PVIntRef, PVStrRef, IntSlot, KVContext
    from every_pv.morphisms import GetOp, SetCmd
"""

# Context
from every_pv.context import KVContext, SingularContext

# Morphisms
from every_pv.morphisms import (
    AddValueCmd,
    AppendValueCmd,
    ChangeOp,
    ClearCmd,
    CountOfValueOp,
    DeleteCmd,
    DiscardValueCmd,
    ExistsOp,
    ExtractOp,
    FilterItemsOp,
    FilterOp,
    FindByPredicateOp,
    FindIndexByPredicateOp,
    FindItemByPredicateOp,
    FindKeyByPredicateOp,
    FindValueByPredicateOp,
    GetByKeyOp,
    GetOp,
    IndexOfValueOp,
    InsertAtIndexCmd,
    ItemsOp,
    KeysOp,
    LengthOp,
    MapItemsOp,
    MapOp,
    MapValuesOp,
    MissingOp,
    OnChangeOp,
    OnChildChangeOp,
    OnChildrenChangeOp,
    OnDescendantsChangeOp,
    OnPrimitiveChangeOp,
    PopByIndexCmd,
    ReduceItemsOp,
    ReduceOp,
    RemoveByKeyCmd,
    RemoveValueCmd,
    SetByKeyCmd,
    SetCmd,
    StoreCmd,
    TypedSetCmd,
    ValuesOp,
)

# Protocols
from every_pv.protocols import (
    PVClearable,
    PVDeletable,
    PVExistable,
    PVExtractable,
    PVGettable,
    PVLengthable,
    PVSettable,
    PVStorable,
)

# Concrete PV refs
from every_pv.pv import (
    PVBoolRef,
    PVBytesRef,
    PVDictItemRef,
    PVDictRef,
    PVFloatRef,
    PVIntRef,
    PVItemRef,
    PVListItemRef,
    PVListRef,
    PVShapeRef,
    PVShapesDictRef,
    PVShapesListRef,
    PVStrRef,
)

# Abstract ref classes
from every_pv.ref import (
    PrimitiveRef,
    ViewRef,
)

# Slots
from every_pv.slots import (
    BoolSlot,
    BytesSlot,
    DictSlot,
    FloatSlot,
    IntSlot,
    ItemSlot,
    ListSlot,
    ShapesDictSlot,
    ShapesListSlot,
    ShapeSlot,
    StrSlot,
)

# Traits
from every_pv.traits import (
    AppendableBase,
    ClearableBase,
    CollectionGettableBase,
    DeletableBase,
    ExistableBase,
    ExtractableBase,
    GettableBase,
    InsertableBase,
    ItemsQueryableBase,
    KeysQueryableBase,
    LengthableBase,
    MappingAccessibleBase,
    MappingIterableBase,
    MappingNestableBase,
    PoppableBase,
    PrimitiveObservableBase,
    SequenceIndexableBase,
    SequenceIterableBase,
    SetAddableBase,
    SetRemovableBase,
    SettableBase,
    StorableBase,
    ValuesQueryableBase,
    ViewObservableBase,
)

# Combined ref bases (for extending)
from every_pv.traits.bases_collections import (
    MappingRefBase,
    MutableMappingRefBase,
    MutableSequenceRefBase,
    MutableSetRefBase,
    SequenceRefBase,
    SetRefBase,
)
from every_pv.traits.bases_primitive import (
    CollectionItemRefBase,
    MappingItemRefBase,
    MutableMappingItemRefBase,
    MutableSequenceItemRefBase,
    SequenceItemRefBase,
)

from . import slots


__all__ = [  # noqa: RUF022
    # Modules
    "slots",
    # Context
    "KVContext",
    "SingularContext",
    # Morphisms - Core access
    "ExistsOp",
    "ExtractOp",
    "GetOp",
    "LengthOp",
    "MissingOp",
    # Morphisms - Core mutate
    "ClearCmd",
    "DeleteCmd",
    "SetCmd",
    "StoreCmd",
    "TypedSetCmd",
    # Morphisms - Sequence
    "AppendValueCmd",
    "CountOfValueOp",
    "FilterOp",
    "FindByPredicateOp",
    "FindIndexByPredicateOp",
    "IndexOfValueOp",
    "InsertAtIndexCmd",
    "MapOp",
    "PopByIndexCmd",
    "ReduceOp",
    # Morphisms - Mapping
    "FilterItemsOp",
    "FindItemByPredicateOp",
    "FindKeyByPredicateOp",
    "FindValueByPredicateOp",
    "GetByKeyOp",
    "ItemsOp",
    "KeysOp",
    "MapItemsOp",
    "MapValuesOp",
    "ReduceItemsOp",
    "RemoveByKeyCmd",
    "SetByKeyCmd",
    "ValuesOp",
    # Morphisms - Set
    "AddValueCmd",
    "DiscardValueCmd",
    "RemoveValueCmd",
    # Morphisms - Reactive
    "ChangeOp",
    "OnChangeOp",
    "OnChildChangeOp",
    "OnChildrenChangeOp",
    "OnDescendantsChangeOp",
    "OnPrimitiveChangeOp",
    # Protocols
    "PVClearable",
    "PVDeletable",
    "PVExistable",
    "PVExtractable",
    "PVGettable",
    "PVLengthable",
    "PVSettable",
    "PVStorable",
    # Concrete PV refs - Primitives
    "PVBoolRef",
    "PVBytesRef",
    "PVDictItemRef",
    "PVFloatRef",
    "PVIntRef",
    "PVItemRef",
    "PVListItemRef",
    "PVStrRef",
    # Concrete PV refs - Collections
    "PVDictRef",
    "PVListRef",
    "PVShapeRef",
    "PVShapesDictRef",
    "PVShapesListRef",
    # Slots
    "BoolSlot",
    "BytesSlot",
    "DictSlot",
    "FloatSlot",
    "IntSlot",
    "ItemSlot",
    "ListSlot",
    "ShapeSlot",
    "ShapesDictSlot",
    "ShapesListSlot",
    "StrSlot",
    # Abstract refs
    "PrimitiveRef",
    "ViewRef",
    # Traits - Core
    "ClearableBase",
    "CollectionGettableBase",
    "DeletableBase",
    "ExistableBase",
    "ExtractableBase",
    "GettableBase",
    "LengthableBase",
    "SettableBase",
    "StorableBase",
    # Traits - Sequence
    "AppendableBase",
    "InsertableBase",
    "PoppableBase",
    "SequenceIndexableBase",
    "SequenceIterableBase",
    # Traits - Mapping
    "MappingAccessibleBase",
    "MappingIterableBase",
    "MappingNestableBase",
    # Traits - Set
    "SetAddableBase",
    "SetRemovableBase",
    # Traits - Query
    "ItemsQueryableBase",
    "KeysQueryableBase",
    "ValuesQueryableBase",
    # Traits - Observable
    "PrimitiveObservableBase",
    "ViewObservableBase",
    # Combined ref bases
    "CollectionItemRefBase",
    "MappingItemRefBase",
    "MappingRefBase",
    "MutableMappingItemRefBase",
    "MutableMappingRefBase",
    "MutableSequenceItemRefBase",
    "MutableSequenceRefBase",
    "MutableSetRefBase",
    "SequenceItemRefBase",
    "SequenceRefBase",
    "SetRefBase",
]
