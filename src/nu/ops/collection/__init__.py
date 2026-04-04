"""Collection operations — combine, reduce, slice, transform."""

from .combine import ChainOp, EnumerateOp, ZipOp
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
    "FilterByOp",
    "FlattenOp",
    "MaxOp",
    "MinOp",
    "PluckOp",
    "ReversedOp",
    "SortedOp",
    "SumOp",
    "TakeOp",
    "UniqueOp",
    "ZipOp",
]
