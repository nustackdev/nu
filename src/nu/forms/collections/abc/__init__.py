"""Generic collection interfaces and ops."""

from .collection import CollectionForm
from .container import ContainerForm
from .iterable import IterableForm
from .mapping import MappingForm, MutableMappingForm
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
from .sequence import MutableSequenceForm, SequenceForm
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
from .set_ import MutableSetForm, SetLikeForm
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
from .sized import SizedForm
from .sliceable import SliceableForm


__all__ = [
    "AddCmd",
    "AppendCmd",
    "ClearCmd",
    "CollectionForm",
    "ContainerForm",
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
    "IterableForm",
    "KeysOp",
    "LastOp",
    "MappingForm",
    "MutableMappingForm",
    "MutableSequenceForm",
    "MutableSetForm",
    "PopCmd",
    "PopItemCmd",
    "RemoveCmd",
    "RemoveValueCmd",
    "ReverseCmd",
    "SequenceForm",
    "SetDefaultCmd",
    "SetItemCmd",
    "SetLikeForm",
    "SetPopCmd",
    "SetUpdateCmd",
    "SizedForm",
    "SliceableForm",
    "SymmetricDifferenceOp",
    "SymmetricDifferenceUpdateCmd",
    "UnionOp",
    "UpdateCmd",
    "ValuesOp",
]
