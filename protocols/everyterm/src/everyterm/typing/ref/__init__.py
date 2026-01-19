"""Ref capabilities.

- Definitions of capabilites
- Definitions of common collections
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
    CollectionItemRef,
    CollectionRef,
    ContainerRef,
    MappingRef,
    MutableMappingRef,
    MutableSequenceRef,
    MutableSetRef,
    SequenceRef,
    SetRef,
)


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
    "CollectionItemRef",
]
