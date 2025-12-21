"""Core implementation of terms, ergonomics, etc."""

from .collections_ergonomics import CollectionsMixin
from .combiners import all_, and_, any_, none_, or_
from .mapping_ops import (
    ContainsOp,
    DictGetOp,
    DictItemsOp,
    DictKeysOp,
    DictValuesOp,
)
from .sequence_ops import (
    AllOp,
    AnyOp,
    AtOp,
    FilterOp,
    FirstOp,
    JoinOp,
    LastOp,
    LenOp,
    MapOp,
    MaxOp,
    MinOp,
    ReduceOp,
    ReversedOp,
    SliceOp,
    SortedOp,
    SumOp,
)


__all__ = [  # noqa: RUF022
    # Combiners
    "all_",
    "and_",
    "any_",
    "none_",
    "or_",
    # Collections mixin
    "CollectionsMixin",
    # Sequence operations
    "AllOp",
    "AnyOp",
    "AtOp",
    "FirstOp",
    "JoinOp",
    "LastOp",
    "LenOp",
    "MaxOp",
    "MinOp",
    "ReversedOp",
    "SliceOp",
    "SortedOp",
    "SumOp",
    # Functional operations
    "FilterOp",
    "MapOp",
    "ReduceOp",
    # Mapping operations
    "ContainsOp",
    "DictGetOp",
    "DictItemsOp",
    "DictKeysOp",
    "DictValuesOp",
]
