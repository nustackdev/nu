"""LValue system - storage location references.

This module provides the foundational LValue system for the everyshape
data layer. LValues represent locations in storage that can be accessed
lazily through operations.

Hierarchy:
    LValueBase
    └── RefBase
        ├── PrimitiveRefBase (leaf value refs)
        └── ViewRefBase (container refs)

Key components:
    - capabilities: Atomic capability protocols (Gettable, Settable, etc.)
    - refs: Reference type protocols (ValueRef, SequenceRef, MappingRef)
    - base: LValueBase, RefBase, PrimitiveRefBase, ViewRefBase
    - bases: Reusable behavior mixins (GettableBase, ExtractableBase, etc.)

Key difference from RValues:
    - LValues are LOCATIONS in storage (lazy access)
    - RValues are ALREADY COMPUTED values in memory

Example:
    >>> from everyshape.lvalue import PrimitiveRefBase, ViewRefBase
    >>> from everyshape.lvalue.refs import ValueRefProtocol
    >>> from everyshape.lvalue.capabilities import is_gettable
"""

# Bases (mixins)
from .bases import (
    ChildObservableBase,
    ClearableBase,
    DeletableBase,
    ExistableBase,
    ExtractableBase,
    GettableBase,
    LengthableBase,
    MappingOpsBase,
    ObservableBase,
    SequenceOpsBase,
    SettableBase,
    StorableBase,
)

# Capabilities
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

# Refs protocols
from .refs import (
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


__all__ = [  # noqa: RUF022
    # Capabilities
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
    # Ref protocols
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
    # Base
    "LValueBase",
    "RefBase",
    "PrimitiveRefBase",
    "ViewRefBase",
    # Bases (mixins)
    "GettableBase",
    "SettableBase",
    "DeletableBase",
    "ExtractableBase",
    "StorableBase",
    "ClearableBase",
    "ExistableBase",
    "ObservableBase",
    "ChildObservableBase",
    "LengthableBase",
    "SequenceOpsBase",
    "MappingOpsBase",
]
