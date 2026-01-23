"""Protocol definitions for everybase.

Protocols define structural type contracts for capabilities.
Use isinstance() checks or typing.Protocol for duck typing.

Structure:
- capabilities.py: Storage capability protocols (Gettable, Settable, etc.)
- collections.py: Collection ref protocol hierarchy (SequenceRef, MappingRef, etc.)

Capabilities (storage operations):
    READ: Gettable, Extractable
    WRITE: Settable, Storable, Appendable, Insertable
    DELETE: Deletable, Clearable, Poppable
    EXISTENCE: Existable
    OBSERVE: RefObservable, RefChildObservable, RefDescendantsObservable
    NAVIGATION: Nestable, RefIndexable, RefSliceable
    QUERY: Lengthable, KeysQueryable, ValuesQueryable, ItemsQueryable
    MAPPING: MappingAccessible

Collection Protocols (ref hierarchy):
    ContainerRef → CollectionRef
        ├── SequenceRef → MutableSequenceRef
        ├── MappingRef → MutableMappingRef
        └── SetRef → MutableSetRef
"""

from __future__ import annotations

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
    MappingAccessible,
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
    # Type guards
    is_clearable,
    is_deletable,
    is_existable,
    is_extractable,
    is_gettable,
    is_lengthable,
    is_mapping_accessible,
    is_ref_indexable,
    is_ref_observable,
    is_settable,
    is_storable,
)

# Collection ref protocols
from .collections import (
    CollectionItemRef,
    CollectionRef,
    ContainerRef,
    MappingRef,
    MutableMappingRef,
    MutableSequenceRef,
    MutableSetLikeRef,
    SequenceRef,
    SetLikeRef,
)


__all__ = [  # noqa: RUF022
    # =========================================================================
    # CAPABILITY PROTOCOLS
    # =========================================================================
    # Read
    "Gettable",
    "Extractable",
    # Write
    "Settable",
    "Storable",
    "Appendable",
    "Insertable",
    # Delete
    "Deletable",
    "Clearable",
    "Poppable",
    # Existence
    "Existable",
    # Observable
    "RefObservable",
    "RefChildObservable",
    "RefDescendantsObservable",
    # Navigation
    "Nestable",
    "RefIndexable",
    "RefSliceable",
    # Query
    "Lengthable",
    "KeysQueryable",
    "ValuesQueryable",
    "ItemsQueryable",
    # Mapping access
    "MappingAccessible",
    # Type guards
    "is_gettable",
    "is_extractable",
    "is_settable",
    "is_storable",
    "is_deletable",
    "is_clearable",
    "is_existable",
    "is_ref_observable",
    "is_ref_indexable",
    "is_lengthable",
    "is_mapping_accessible",
    # =========================================================================
    # COLLECTION REF PROTOCOLS
    # =========================================================================
    # Base
    "ContainerRef",
    "CollectionRef",
    # Sequence
    "SequenceRef",
    "MutableSequenceRef",
    # Mapping
    "MappingRef",
    "MutableMappingRef",
    # Set
    "SetLikeRef",
    "MutableSetLikeRef",
    # Item
    "CollectionItemRef",
]
