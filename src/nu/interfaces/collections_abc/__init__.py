"""Generic collection protocols and ops."""

from .collection import CollectionBase, CollectionProtocol
from .iterable import IterableBase, IterableProtocol
from .mapping import MappingBase, MappingProtocol, MutableMappingBase, MutableMappingProtocol
from .mapping_ops import (
    CopyOp,
    DeleteItemCmd,
    DictPopCmd,
    GetOp,
    ItemsOp,
    KeyAtOp,
    KeysOp,
    PopItemCmd,
    SetDefaultCmd,
    SetItemCmd,
    UpdateCmd,
    ValuesOp,
)
from .sequence import MutableSequenceBase, MutableSequenceProtocol, SequenceBase, SequenceProtocol
from .sequence_ops import (
    AppendCmd,
    CountOp,
    ExtendCmd,
    FirstOp,
    IndexOfOp,
    InsertCmd,
    JoinOp,
    LastOp,
    PopCmd,
    RemoveValueCmd,
)
from .set_ import MutableSetBase, MutableSetProtocol, SetLikeBase, SetLikeProtocol
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
