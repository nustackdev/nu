"""LValue system - storage location references.

This module provides the foundational LValue system for the everyshape
data layer. LValues represent locations in storage that can be accessed
lazily through operations.

Module Structure:
    capabilities.py     - Capability PROTOCOLS (Gettable, Settable, etc.)
    collections.py      - Collection ref PROTOCOLS (SequenceRefProtocol, etc.)
    base.py             - Base classes (PrimitiveRefBase, ViewRefBase)
    bases.py            - Capability implementation MIXINS (GettableBase, etc.)
    refs.py             - Complete ref IMPLEMENTATIONS (MappingRefImpl, etc.)

Hierarchy:
    PROTOCOLS (what things CAN do):
        capabilities.py: Gettable, Settable, Existable, Extractable, ...
        collections.py: RefProtocol, SequenceRefProtocol, MappingRefProtocol, ...

    IMPLEMENTATIONS (HOW things do it):
        base.py: PrimitiveRefBase, ViewRefBase
        bases.py: GettableBase, SettableBase, ExistableBase, ...
        refs.py: PrimitiveRefImpl, MappingRefImpl, SequenceRefImpl, ...

Key difference from RValues:
    - LValues are LOCATIONS in storage (lazy access)
    - RValues are ALREADY COMPUTED values in memory

Example:
    >>> from everyshape.shape.refs import MappingRefImpl, PrimitiveRefImpl
    >>> from everyshape.shape.refs.collections import MappingRefProtocol
    >>> from everyshape.shape.refs.capabilities import Gettable
    >>> from everyshape.shape.refs.bases import GettableBase
"""

from __future__ import annotations

# Base classes
from .base import (
    PrimitiveRefBase,
    ViewRefBase,
)

# Capability implementation mixins
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
    MappingRefProtocol,
    MutableMappingRefProtocol,
    MutableSequenceRefProtocol,
    MutableSetRefProtocol,
    PrimitiveRefProtocol,
    RefProtocol,
    SequenceRefProtocol,
    SetRefProtocol,
    ValueRefProtocol,
    ViewRefProtocol,
)

# Complete ref implementations (from refs.py)
from .refs import (
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
    # COLLECTION REF PROTOCOLS
    # ==========================================================================
    "RefProtocol",
    "PrimitiveRefProtocol",
    "ValueRefProtocol",
    "ViewRefProtocol",
    "SequenceRefProtocol",
    "MutableSequenceRefProtocol",
    "MappingRefProtocol",
    "MutableMappingRefProtocol",
    "SetRefProtocol",
    "MutableSetRefProtocol",
    # ==========================================================================
    # BASE CLASSES
    # ==========================================================================
    "PrimitiveRefBase",
    "ViewRefBase",
    # ==========================================================================
    # CAPABILITY IMPLEMENTATION MIXINS
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
    # Set capability bases
    "SetAddableBase",
    "SetRemovableBase",
    # ==========================================================================
    # COMPLETE REF IMPLEMENTATIONS
    # ==========================================================================
    "SequenceRef",
    "MutableSequenceRef",
    "MappingRef",
    "MutableMappingRef",
    "SetRef",
    "MutableSetRef",
]
