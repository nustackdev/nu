"""Capability implementation bases for LValue references.

This module provides mixin classes that IMPLEMENT capability protocols.
These are the building blocks that get combined to create
complete ref implementations.

Each base implements methods from the corresponding capability protocol:
- ExistableBase implements Existable (exists(), missing())
- GettableBase implements Gettable (get())
- SettableBase implements Settable (set())
- etc.

These are NOT protocols - they are concrete implementations that can be
mixed into ref classes.

Usage:
    class MyRef(ExistableBase, GettableBase, SettableBase, PrimitiveRef):
        # Gets exists(), missing(), get(), set() implementations
        pass
"""

from .core import (
    ClearableBase,
    DeletableBase,
    ExistableBase,
    ExtractableBase,
    GettableBase,
    LengthableBase,
    SettableBase,
    StorableBase,
)
from .mapping import (
    MappingAccessibleBase,
    MappingIterableBase,
    MappingNestableBase,
)
from .observable import (
    PrimitiveObservableBase,
    ViewObservableBase,
)
from .query import (
    ItemsQueryableBase,
    KeysQueryableBase,
    ValuesQueryableBase,
)
from .sequence import (
    AppendableBase,
    InsertableBase,
    PoppableBase,
    SequenceIndexableBase,
    SequenceIterableBase,
)
from .set import (
    SetAddableBase,
    SetRemovableBase,
)


__all__ = [
    "AppendableBase",
    "ClearableBase",
    "DeletableBase",
    "ExistableBase",
    "ExtractableBase",
    "GettableBase",
    "InsertableBase",
    "ItemsQueryableBase",
    "KeysQueryableBase",
    "LengthableBase",
    "MappingAccessibleBase",
    "MappingIterableBase",
    "MappingNestableBase",
    "PoppableBase",
    "PrimitiveObservableBase",
    "SequenceIndexableBase",
    "SequenceIterableBase",
    "SetAddableBase",
    "SetRemovableBase",
    "SettableBase",
    "StorableBase",
    "UnionRefBases",
    "ValuesQueryableBase",
    "ViewObservableBase",
]


type UnionRefBases = (
    ExistableBase
    | GettableBase
    | SettableBase
    | DeletableBase
    | ExtractableBase
    | StorableBase
    | ClearableBase
    | LengthableBase
    | PrimitiveObservableBase
    | ViewObservableBase
    | KeysQueryableBase
    | ValuesQueryableBase
    | ItemsQueryableBase
    | SequenceIndexableBase
    | SequenceIterableBase
    | AppendableBase
    | InsertableBase
    | PoppableBase
    | MappingNestableBase
    | MappingIterableBase
    | MappingAccessibleBase
    | SetAddableBase
    | SetRemovableBase
)
