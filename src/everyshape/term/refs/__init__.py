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
    >>> from everyshape.term.refs import MappingRefBase, ValueRef
    >>> from everyshape.term.refs import MappingRef  # Protocol
    >>> from everyshape.term.refs import Gettable, GettableBase
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
    MappingValueRefBase,
    MutableMappingValueRefBase,
    MutableSequenceValueRefBase,
    SequenceValueRefBase,
    ValueRefBase,
)

# Capability protocols
from .capabilities import (
    Appendable,
    Clearable,
    Deletable,
    Existable,
    Extractable,
    Gettable,
    Insertable,
    ItemsQueryable,
    KeysQueryable,
    Lengthable,
    Nestable,
    Poppable,
    RefChildObservable,
    RefDescendantsObservable,
    RefIndexable,
    RefObservable,
    RefSliceable,
    Settable,
    Storable,
    ValuesQueryable,
    is_clearable,
    is_deletable,
    is_existable,
    is_extractable,
    is_gettable,
    is_lengthable,
    is_ref_indexable,
    is_ref_observable,
    is_settable,
    is_storable,
)

# Collection ref protocols (from collections.py)
from .collections import (
    CollectionRef,
    ContainerRef,
    MappingRef,
    MutableMappingRef,
    MutableSequenceRef,
    MutableSetRef,
    PrimitiveRef,
    SequenceRef,
    SetRef,
)
from .collections import ValueRef as ValueRefProtocol


__all__ = [  # noqa: RUF022
    # ==========================================================================
    # CAPABILITY PROTOCOLS
    # ==========================================================================
    "Appendable",
    "Clearable",
    "Deletable",
    "Existable",
    "Extractable",
    "Gettable",
    "Insertable",
    "ItemsQueryable",
    "KeysQueryable",
    "Lengthable",
    "Nestable",
    "Poppable",
    "RefChildObservable",
    "RefDescendantsObservable",
    "RefIndexable",
    "RefObservable",
    "RefSliceable",
    "Settable",
    "Storable",
    "ValuesQueryable",
    # Type guards
    "is_clearable",
    "is_deletable",
    "is_existable",
    "is_extractable",
    "is_gettable",
    "is_lengthable",
    "is_ref_indexable",
    "is_ref_observable",
    "is_settable",
    "is_storable",
    # ==========================================================================
    # COLLECTION REF PROTOCOLS (from collections.py)
    # ==========================================================================
    # Base protocols
    "ContainerRef",
    "CollectionRef",
    # Sequence protocols
    "SequenceRef",
    "MutableSequenceRef",
    # Mapping protocols
    "MappingRef",
    "MutableMappingRef",
    # Set protocols
    "SetRef",
    "MutableSetRef",
    # Primitive protocols
    "PrimitiveRef",
    "ValueRefProtocol",
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
    # Set capability bases
    "SetAddableBase",
    "SetRemovableBase",
    # Combined primitive ref bases
    "ValueRefBase",
    "SequenceValueRefBase",
    "MutableSequenceValueRefBase",
    "MappingValueRefBase",
    "MutableMappingValueRefBase",
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
