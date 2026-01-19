"""LValue system - storage location references.

This module provides the foundational LValue system for the everyshape
data layer. LValues represent locations in storage that can be accessed
lazily through operations.

Module Structure:
    capabilities.py     - Capability PROTOCOLS (Gettable, Settable, etc.)
    collections.py      - Collection ref PROTOCOLS (SequenceRef, MappingRef, etc.)
    bases.py            - Capability implementation MIXINS (GettableBase, ValueRefBase, etc.)
    refs.py             - Complete ref BASE CLASSES (SequenceRefBase, MappingRefBase, etc.)
    primitive_refs.py   - Primitive value refs (ValueRef, SequenceValueRef, etc.)

Protocol Hierarchy (collections.py):
    Ref (base)
    ├── ContainerRef (existence checking)
    │   └── CollectionRef (sized, extractable, storable)
    │       ├── SequenceRef[T] (indexed access)
    │       │   └── MutableSequenceRef[T]
    │       ├── MappingRef[K,V] (key access)
    │       │   └── MutableMappingRef[K,V]
    │       └── SetRef[T] (containment)
    │           └── MutableSetRef[T]
    └── PrimitiveRef[T] (leaf value references)
        └── ValueRef[T] (typed primitive value)

Implementation Hierarchy:
    bases.py: Atomic mixins (ExistableBase, GettableBase, etc.)
              Combined primitive bases (ValueRefBase, SequenceValueRefBase, etc.)
    refs.py:  View ref bases (SequenceRefBase, MappingRefBase, SetRefBase, etc.)

Key difference from RValues:
    - LValues are LOCATIONS in storage (lazy access)
    - RValues are ALREADY COMPUTED values in memory

Example:
    >>> from everybase.term.refs import MappingRefBase, ValueRef
    >>> from everybase.term.refs import MappingRef  # Protocol
    >>> from everybase.term.refs import Gettable, GettableBase
"""

from __future__ import annotations

# Capability implementation mixins (atomic)
from .bases import (
    AppendableBase,
    ClearableBase,
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
    UnionRefBases,
    ValuesQueryableBase,
    ViewObservableBase,
)
from .bases_collections import (
    MappingRefBase,
    MutableMappingRefBase,
    MutableSequenceRefBase,
    MutableSetRefBase,
    SequenceRefBase,
    SetRefBase,
)
from .bases_primitive import (
    CollectionItemRefBase,
    MappingItemRefBase,
    MutableMappingItemRefBase,
    MutableSequenceItemRefBase,
    SequenceItemRefBase,
)
from .collections import DictRef, ListRef, ShapeRef, ShapesDictRef, ShapesListRef
from .primitives import (
    BoolRef,
    BytesRef,
    DictItemRef,
    FloatRef,
    IntRef,
    ItemRef,
    ListItemRef,
    StrRef,
)


__all__ = [  # noqa: RUF022
    # ==========================================================================
    # CONCRETE REFS
    # ==========================================================================
    "DictRef",
    "ListRef",
    "ShapeRef",
    "ShapesListRef",
    "ShapesDictRef",
    "ItemRef",
    "DictItemRef",
    "ListItemRef",
    "IntRef",
    "StrRef",
    "FloatRef",
    "BoolRef",
    "BytesRef",
    # ==========================================================================
    # CAPABILITY IMPLEMENTATION MIXINS (from bases.py)
    # ==========================================================================
    "UnionRefBases",
    # Core capability bases
    "ExistableBase",
    "GettableBase",
    "SettableBase",
    "DeletableBase",
    "ExtractableBase",
    "StorableBase",
    "ClearableBase",
    "LengthableBase",
    # Observable bases
    "PrimitiveObservableBase",
    "ViewObservableBase",
    # Query bases
    "KeysQueryableBase",
    "ValuesQueryableBase",
    "ItemsQueryableBase",
    # Sequence capability bases
    "SequenceIndexableBase",
    "SequenceIterableBase",
    "AppendableBase",
    "InsertableBase",
    "PoppableBase",
    # Mapping capability bases
    "MappingNestableBase",
    "MappingIterableBase",
    "MappingAccessibleBase",
    # Set capability bases
    "SetAddableBase",
    "SetRemovableBase",
    # Combined primitive ref bases
    "CollectionItemRefBase",
    "MappingItemRefBase",
    "MutableMappingItemRefBase",
    "MutableSequenceItemRefBase",
    "SequenceItemRefBase",
    # ==========================================================================
    # VIEW REF BASE IMPLEMENTATIONS (from refs.py)
    # ==========================================================================
    "SequenceRefBase",
    "MutableSequenceRefBase",
    "MappingRefBase",
    "MutableMappingRefBase",
    "SetRefBase",
    "MutableSetRefBase",
]
