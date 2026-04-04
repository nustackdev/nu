"""Functional itertools — typed factories returning Interface types."""

from .combine import Chain, Enumerate, Zip
from .group import GroupBy, Partition
from .reduce import All, Any, Max, Min, Reduce, Sum
from .slice import Drop, Take
from .transform import (
    Filter,
    FilterBy,
    Flatten,
    Map,
    Pluck,
    Reversed,
    Sorted,
    ToDict,
    Unique,
)


__all__ = [
    "All",
    "Any",
    "Chain",
    "Drop",
    "Enumerate",
    "Filter",
    "FilterBy",
    "Flatten",
    "GroupBy",
    "Map",
    "Max",
    "Min",
    "Partition",
    "Pluck",
    "Reduce",
    "Reversed",
    "Sorted",
    "Sum",
    "Take",
    "ToDict",
    "Unique",
    "Zip",
]
