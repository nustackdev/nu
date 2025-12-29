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

# Commands (from computations)
from ..computations.commands import (
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

# Reactive operations (from computations)
from ..computations.reactive_ops import (
    ChangeOp,
    OnChangeOp,
    OnChildChangeOp,
    OnChildrenChangeOp,
    OnDescendantsChangeOp,
    OnPrimitiveChangeOp,
)

# Operations (from computations)
from ..computations.ref_ops import (
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

# Base classes (from base.py)
from .base import (
    PrimitiveRefBase,
    ViewRefBase,
)

# Capability implementation mixins (from bases.py)
from .bases import (
    AppendableBase,
    ClearableBase,
    DeletableBase,
    # Core capability bases
    ExistableBase,
    ExtractableBase,
    GettableBase,
    InsertableBase,
    ItemsQueryableBase,
    # Query bases
    KeysQueryableBase,
    LengthableBase,
    PoppableBase,
    # Observable bases
    PrimitiveObservableBase,
    # Sequence capability bases
    SequenceIndexableBase,
    SequenceIterableBase,
    # Set capability bases
    SetAddableBase,
    SetRemovableBase,
    SettableBase,
    StorableBase,
    ValuesQueryableBase,
    ViewObservableBase,
)

# Capability protocols (from capabilities.py)
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
    MappingRefImpl,
    MutableMappingRefImpl,
    MutableSequenceRefImpl,
    MutableSetRefImpl,
    PrimitiveRefImpl,
    SequenceRefImpl,
    SetRefImpl,
)


__all__ = [  # noqa: RUF022
    # ==========================================================================
    # CAPABILITY PROTOCOLS (from capabilities.py)
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
    # BASE CLASSES (from base.py)
    # ==========================================================================
    "PrimitiveRefBase",
    "ViewRefBase",
    # ==========================================================================
    # CAPABILITY IMPLEMENTATION MIXINS (from bases.py)
    # ==========================================================================
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
    # COMPLETE REF IMPLEMENTATIONS (from refs.py)
    # ==========================================================================
    "PrimitiveRefImpl",
    "SequenceRefImpl",
    "MutableSequenceRefImpl",
    "MappingRefImpl",
    "MutableMappingRefImpl",
    "SetRefImpl",
    "MutableSetRefImpl",
    # ==========================================================================
    # OPERATIONS (from computations)
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
    # Reactive
    "ChangeOp",
    "OnChangeOp",
    "OnChildChangeOp",
    "OnChildrenChangeOp",
    "OnDescendantsChangeOp",
    "OnPrimitiveChangeOp",
    # ==========================================================================
    # COMMANDS (from computations)
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
