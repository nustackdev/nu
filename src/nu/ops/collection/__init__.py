"""Collection operations — combine, reduce, slice, transform, iteration."""

from .combine import ChainOp, EnumerateOp, ZipOp
from .iteration import Filter, Map, TakeWhile, Unique
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
    "FlattenOp",
    "Map",
    "MaxOp",
    "MinOp",
    "PluckOp",
    "ReversedOp",
    "SortedOp",
    "SumOp",
    "TakeOp",
    "TakeWhile",
    "Unique",
    "UniqueOp",
    "ZipOp",
]
