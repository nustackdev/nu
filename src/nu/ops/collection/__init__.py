"""Collection operations — combine, reduce, slice, transform, iteration."""

from .combine import ChainOp, EnumerateOp, ZipOp
from .iteration import Filter, Find, FindIndex, GroupBy, Map, Partition, TakeWhile, ToDict, Unique
from .reduce import AllOp, AnyOp, MaxOp, MinOp, SumOp
from .slice import DropOp, TakeOp
from .transform import (
    FilterByOp,
    FlattenOp,
    PluckOp,
    ReversedOp,
    SortedOp,
    UniqueOp,
)


__all__ = [
    "AllOp",
    "AnyOp",
    "ChainOp",
    "DropOp",
    "EnumerateOp",
    "Filter",
    "FilterByOp",
    "Find",
    "FindIndex",
    "FlattenOp",
    "GroupBy",
    "Map",
    "MaxOp",
    "MinOp",
    "Partition",
    "PluckOp",
    "ReversedOp",
    "SortedOp",
    "SumOp",
    "TakeOp",
    "TakeWhile",
    "ToDict",
    "Unique",
    "UniqueOp",
    "ZipOp",
]
