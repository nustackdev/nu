"""LValue system - storage location references.

This module provides the foundational LValue system for the everyshape
data layer. LValues represent locations in storage that can be accessed
lazily through operations.

Hierarchy:
    LValueBase
    └── RefBase
        ├── PrimitiveRefBase (leaf value refs)
        └── ViewRefBase (container refs)
            ├── SequenceRefBase / MutableSequenceRefBase
            ├── MappingRefBase / MutableMappingRefBase
            └── SetRefBase / MutableSetRefBase

Key components:
    - capabilities: Atomic capability protocols (Gettable, Settable, etc.)
    - refs: Reference type protocols (ValueRef, SequenceRef, MappingRef)
    - bases: Complete ref implementations (PrimitiveRefBase, MappingRefBase, etc.)
    - operations: Concrete operation classes (GetOp, ExtractOp, MapOp, etc.)
    - commands: Concrete command classes (SetCmd, DeleteCmd, AppendCmd, etc.)

Key difference from RValues:
    - LValues are LOCATIONS in storage (lazy access)
    - RValues are ALREADY COMPUTED values in memory

Example:
    >>> from everyshape.shape.refs import PrimitiveRefBase, MappingRefBase
    >>> from everyshape.shape.refs.refs import ValueRefProtocol
    >>> from everyshape.shape.refs.capabilities import is_gettable
    >>> from everyshape.shape.refs.operations import GetOp
    >>> from everyshape.shape.refs.commands import SetCmd
"""

# Bases (complete ref implementations)
from .bases import (
    MappingRefBase,
    MutableMappingRefBase,
    MutableSequenceRefBase,
    MutableSetRefBase,
    PrimitiveRefBase,
    SequenceRefBase,
    SetRefBase,
    ViewRefBase,
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

# Commands
from .commands import (
    AddCmd,
    AppendCmd,
    ClearCmd,
    DeleteCmd,
    DiscardCmd,
    InsertCmd,
    PopCmd,
    RemoveCmd,
    SetCmd,
    StoreCmd,
)

# Operations
from .operations import (
    CountOp,
    ExistsOp,
    ExtractOp,
    FilterItemsOp,
    FilterOp,
    FindIndexOp,
    FindItemOp,
    FindKeyOp,
    FindOp,
    FindValueOp,
    GetOp,
    IndexOp,
    ItemsOp,
    KeysOp,
    LengthOp,
    MapItemsOp,
    MapOp,
    MapValuesOp,
    MissingOp,
    ReduceItemsOp,
    ReduceOp,
    ValuesOp,
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
    # REF TYPE PROTOCOLS
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
    # REF BASES (complete implementations)
    # ==========================================================================
    "PrimitiveRefBase",
    "ViewRefBase",
    "SequenceRefBase",
    "MutableSequenceRefBase",
    "MappingRefBase",
    "MutableMappingRefBase",
    "SetRefBase",
    "MutableSetRefBase",
    # ==========================================================================
    # OPERATIONS (pure computations)
    # ==========================================================================
    # Core operations
    "GetOp",
    "ExtractOp",
    "ExistsOp",
    "MissingOp",
    "LengthOp",
    # Sequence operations
    "MapOp",
    "FilterOp",
    "ReduceOp",
    "IndexOp",
    "CountOp",
    "FindOp",
    "FindIndexOp",
    # Mapping operations
    "KeysOp",
    "ValuesOp",
    "ItemsOp",
    "MapValuesOp",
    "MapItemsOp",
    "FilterItemsOp",
    "ReduceItemsOp",
    "FindKeyOp",
    "FindValueOp",
    "FindItemOp",
    # ==========================================================================
    # COMMANDS (impure mutations)
    # ==========================================================================
    # Core commands
    "SetCmd",
    "DeleteCmd",
    "StoreCmd",
    "ClearCmd",
    # Sequence commands
    "AppendCmd",
    "InsertCmd",
    "PopCmd",
    # Set commands
    "AddCmd",
    "RemoveCmd",
    "DiscardCmd",
]
