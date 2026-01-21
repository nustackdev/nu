"""Reference operations module.

This module provides operations and commands for working with refs (LValues).

Re-exports from:
- core_access: Core read operations (GetOp, ExtractOp, etc.)
- core_mutate: Core mutations (SetCmd, DeleteCmd, etc.)
- sequence: Sequence operations (AppendValueCmd, MapOp, FilterOp, etc.)
- mapping: Mapping operations (SetByKeyCmd, KeysOp, MapValuesOp, etc.)
- set: Set operations (AddValueCmd, RemoveValueCmd, DiscardValueCmd)
"""

from .core_access import (
    ExistsOp,
    ExtractOp,
    GetOp,
    LengthOp,
    MissingOp,
)
from .core_mutate import (
    ClearCmd,
    DeleteCmd,
    SetCmd,
    StoreCmd,
    TypedSetCmd,
)
from .mapping import (
    FilterItemsOp,
    FindItemByPredicateOp,
    FindKeyByPredicateOp,
    FindValueByPredicateOp,
    GetByKeyOp,
    ItemsOp,
    KeysOp,
    MapItemsOp,
    MapValuesOp,
    ReduceItemsOp,
    RemoveByKeyCmd,
    SetByKeyCmd,
    ValuesOp,
)
from .sequence import (
    AppendValueCmd,
    CountOfValueOp,
    FilterOp,
    FindByPredicateOp,
    FindIndexByPredicateOp,
    IndexOfValueOp,
    InsertAtIndexCmd,
    MapOp,
    PopByIndexCmd,
    ReduceOp,
)
from .set import (
    AddValueCmd,
    DiscardValueCmd,
    RemoveValueCmd,
)


__all__ = [  # noqa: RUF022
    # Core access
    "ExistsOp",
    "ExtractOp",
    "GetOp",
    "LengthOp",
    "MissingOp",
    # Core mutate
    "ClearCmd",
    "DeleteCmd",
    "SetCmd",
    "StoreCmd",
    "TypedSetCmd",
    # Sequence
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
    # Mapping
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
    # Set
    "AddValueCmd",
    "DiscardValueCmd",
    "RemoveValueCmd",
]
