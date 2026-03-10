"""Functional iteration morphisms — transform, combine, slice, group, reduce, search."""

from .combine import ChainOp, EnumerateOp, ZipOp
from .group import GroupByOp, PartitionOp
from .reduce import AllOp, AnyOp, MaxOp, MinOp, ReduceOp, SumOp
from .search import FindIndexOp, FindOp
from .slice import DropOp, TakeOp
from .transform import (
    FilterByOp,
    FilterOp,
    FlattenOp,
    MapOp,
    PluckOp,
    ReversedOp,
    SortedOp,
    ToDictOp,
    UniqueOp,
)


__all__ = [
    "AllOp",
    "AnyOp",
    "ChainOp",
    "DropOp",
    "EnumerateOp",
    "FilterByOp",
    "FilterOp",
    "FindIndexOp",
    "FindOp",
    "FlattenOp",
    "GroupByOp",
    "MapOp",
    "MaxOp",
    "MinOp",
    "PartitionOp",
    "PluckOp",
    "ReduceOp",
    "ReversedOp",
    "SortedOp",
    "SumOp",
    "TakeOp",
    "ToDictOp",
    "UniqueOp",
    "ZipOp",
]
