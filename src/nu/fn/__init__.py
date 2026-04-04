"""Functional API — typed factories over ops, returning Interface types.

Builtins: Len, Contains
Conversion: ToInt, ToFloat, ToBool, ToStr, ToBytes, ToList, ToSet
Itertools: Map, Filter, Sorted, Reversed, Flatten, Unique, Pluck, FilterBy,
           Zip, Chain, Enumerate, Take, Drop, GroupBy, Partition,
           Reduce, Sum, Min, Max, Any, All, ToDict
"""

from .builtins import Contains, Len
from .conversion import ToBool, ToBytes, ToFloat, ToInt, ToList, ToSet, ToStr
from .itertools import (
    All,
    Any,
    Chain,
    Drop,
    Enumerate,
    Filter,
    FilterBy,
    Flatten,
    GroupBy,
    Map,
    Max,
    Min,
    Partition,
    Pluck,
    Reduce,
    Reversed,
    Sorted,
    Sum,
    Take,
    ToDict,
    Unique,
    Zip,
)


__all__ = [
    "All",
    "Any",
    "Chain",
    "Contains",
    "Drop",
    "Enumerate",
    "Filter",
    "FilterBy",
    "Flatten",
    "GroupBy",
    "Len",
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
    "ToBool",
    "ToBytes",
    "ToDict",
    "ToFloat",
    "ToInt",
    "ToList",
    "ToSet",
    "ToStr",
    "Unique",
    "Zip",
]
