"""Collection structural morphisms — sequence, mapping, set operations."""

from .mapping import (
    DeleteItemCmd,
    GetOp,
    ItemsOp,
    KeyAtOp,
    KeysOp,
    SetItemCmd,
    UpdateCmd,
    ValuesOp,
)
from .sequence import (
    AppendCmd,
    CountOp,
    ExtendCmd,
    FirstOp,
    IndexOfOp,
    InsertCmd,
    LastOp,
    PopCmd,
    RemoveValueCmd,
)
from .set import (
    AddCmd,
    DifferenceOp,
    DiscardCmd,
    IntersectionOp,
    IsDisjointOp,
    IsSubsetOp,
    IsSupersetOp,
    RemoveCmd,
    SymmetricDifferenceOp,
    UnionOp,
)
from .shared import ClearCmd


__all__ = [
    "AddCmd",
    "AppendCmd",
    "ClearCmd",
    "CountOp",
    "DeleteItemCmd",
    "DifferenceOp",
    "DiscardCmd",
    "ExtendCmd",
    "FirstOp",
    "GetOp",
    "IndexOfOp",
    "InsertCmd",
    "IntersectionOp",
    "IsDisjointOp",
    "IsSubsetOp",
    "IsSupersetOp",
    "ItemsOp",
    "KeyAtOp",
    "KeysOp",
    "LastOp",
    "PopCmd",
    "RemoveCmd",
    "RemoveValueCmd",
    "SetItemCmd",
    "SymmetricDifferenceOp",
    "UnionOp",
    "UpdateCmd",
    "ValuesOp",
]
