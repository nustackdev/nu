"""Computations - operations and commands for shape system."""

from __future__ import annotations

# Commands (from computations)
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

# Reactive operations (from computations)
from .reactive_ops import (
    ChangeOp,
    OnChangeOp,
    OnChildChangeOp,
    OnChildrenChangeOp,
    OnDescendantsChangeOp,
    OnPrimitiveChangeOp,
)

# Operations (from computations)
from .ref_ops import (
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


__all__ = [  # noqa: RUF022
    # ==========================================================================
    # OPERATIONS
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
    # COMMANDS
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
