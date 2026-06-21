"""Generic collection interfaces and interactions."""

from .collection import CollectionForm
from .container import ContainerForm
from .iterable import IterableForm
from .mapping import MappingForm, MutableMappingForm
from .mapping_interactions import (
    DeleteItemQuery,
    DictPopQuery,
    GetQuery,
    ItemsQuery,
    KeysQuery,
    PopItemQuery,
    SetDefaultQuery,
    SetItemQuery,
    UpdateQuery,
    ValuesQuery,
)
from .sequence import MutableSequenceForm, SequenceForm
from .sequence_interactions import (
    AppendQuery,
    CountQuery,
    ExtendQuery,
    FirstQuery,
    IndexOfQuery,
    InsertQuery,
    LastQuery,
    PopQuery,
    RemoveValueQuery,
    ReverseQuery,
)
from .set_ import MutableSetForm, SetLikeForm
from .set_interactions import (
    AddQuery,
    DifferenceQuery,
    DifferenceUpdateQuery,
    DiscardQuery,
    IntersectionQuery,
    IntersectionUpdateQuery,
    IsDisjointQuery,
    IsSubsetQuery,
    IsSupersetQuery,
    RemoveQuery,
    SetPopQuery,
    SetUpdateQuery,
    SymmetricDifferenceQuery,
    SymmetricDifferenceUpdateQuery,
    UnionQuery,
)
from .shared_interactions import ClearQuery
from .sized import SizedForm
from .sliceable import SliceableForm


__all__ = [
    "AddQuery",
    "AppendQuery",
    "ClearQuery",
    "CollectionForm",
    "ContainerForm",
    "CountQuery",
    "DeleteItemQuery",
    "DictPopQuery",
    "DifferenceQuery",
    "DifferenceUpdateQuery",
    "DiscardQuery",
    "ExtendQuery",
    "FirstQuery",
    "GetQuery",
    "IndexOfQuery",
    "InsertQuery",
    "IntersectionQuery",
    "IntersectionUpdateQuery",
    "IsDisjointQuery",
    "IsSubsetQuery",
    "IsSupersetQuery",
    "ItemsQuery",
    "IterableForm",
    "KeysQuery",
    "LastQuery",
    "MappingForm",
    "MutableMappingForm",
    "MutableSequenceForm",
    "MutableSetForm",
    "PopItemQuery",
    "PopQuery",
    "RemoveQuery",
    "RemoveValueQuery",
    "ReverseQuery",
    "SequenceForm",
    "SetDefaultQuery",
    "SetItemQuery",
    "SetLikeForm",
    "SetPopQuery",
    "SetUpdateQuery",
    "SizedForm",
    "SliceableForm",
    "SymmetricDifferenceQuery",
    "SymmetricDifferenceUpdateQuery",
    "UnionQuery",
    "UpdateQuery",
    "ValuesQuery",
]
