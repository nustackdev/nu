"""Generic collection interfaces and ops."""

from .collection import CollectionI
from .container import ContainerI
from .iterable import IterableI
from .mapping import MappingI, MutableMappingI
from .mapping_ops import (
    DeleteItemCmd,
    DictPopCmd,
    GetOp,
    ItemsOp,
    KeysOp,
    PopItemCmd,
    SetDefaultCmd,
    SetItemCmd,
    UpdateCmd,
    ValuesOp,
)
from .sequence import MutableSequenceI, SequenceI
from .sequence_ops import (
    AppendCmd,
    CountOp,
    ExtendCmd,
    FirstOp,
    IndexOfOp,
    InsertCmd,
    LastOp,
    PopCmd,
    RemoveValueCmd,
    ReverseCmd,
)
from .set_ import MutableSetI, SetLikeI
from .set_ops import (
    AddCmd,
    DifferenceOp,
    DifferenceUpdateCmd,
    DiscardCmd,
    IntersectionOp,
    IntersectionUpdateCmd,
    IsDisjointOp,
    IsSubsetOp,
    IsSupersetOp,
    RemoveCmd,
    SetPopCmd,
    SetUpdateCmd,
    SymmetricDifferenceOp,
    SymmetricDifferenceUpdateCmd,
    UnionOp,
)
from .shared_ops import ClearCmd
from .sized import SizedI
from .sliceable import SliceableI


__all__ = [
    "AddCmd",
    "AppendCmd",
    "ClearCmd",
    "CollectionI",
    "ContainerI",
    "CountOp",
    "DeleteItemCmd",
    "DictPopCmd",
    "DifferenceOp",
    "DifferenceUpdateCmd",
    "DiscardCmd",
    "ExtendCmd",
    "FirstOp",
    "GetOp",
    "IndexOfOp",
    "InsertCmd",
    "IntersectionOp",
    "IntersectionUpdateCmd",
    "IsDisjointOp",
    "IsSubsetOp",
    "IsSupersetOp",
    "ItemsOp",
    "IterableI",
    "KeysOp",
    "LastOp",
    "MappingI",
    "MutableMappingI",
    "MutableSequenceI",
    "MutableSetI",
    "PopCmd",
    "PopItemCmd",
    "RemoveCmd",
    "RemoveValueCmd",
    "ReverseCmd",
    "SequenceI",
    "SetDefaultCmd",
    "SetItemCmd",
    "SetLikeI",
    "SetPopCmd",
    "SetUpdateCmd",
    "SizedI",
    "SliceableI",
    "SymmetricDifferenceOp",
    "SymmetricDifferenceUpdateCmd",
    "UnionOp",
    "UpdateCmd",
    "ValuesOp",
]
