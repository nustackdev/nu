"""Functional API — typed factories over ops, returning Interface types.

Builtins: Len, Contains
Conversion: ToInt, ToFloat, ToBool, ToStr, ToBytes, ToList, ToSet
Collection: Sorted, Reversed, Flatten, Unique, Pluck, FilterBy,
            Zip, Chain, Enumerate, Take, Drop,
            Sum, Min, Max, Any, All
Combiners: all_(), any_(), none_(), and_(), or_()
"""

from .builtins import Contains, Len
from .collection import (
    All,
    Any,
    Chain,
    Drop,
    Enumerate,
    FilterBy,
    Flatten,
    Max,
    Min,
    Pluck,
    Reversed,
    Sorted,
    Sum,
    Take,
    Unique,
    Zip,
)
from .combiners import all_, and_, any_, none_, or_
from .conversion import ToBool, ToBytes, ToFloat, ToInt, ToList, ToSet, ToStr


__all__ = [
    "All",
    "Any",
    "Chain",
    "Contains",
    "Drop",
    "Enumerate",
    "FilterBy",
    "Flatten",
    "Len",
    "Max",
    "Min",
    "Pluck",
    "Reversed",
    "Sorted",
    "Sum",
    "Take",
    "ToBool",
    "ToBytes",
    "ToFloat",
    "ToInt",
    "ToList",
    "ToSet",
    "ToStr",
    "Unique",
    "Zip",
    "all_",
    "and_",
    "any_",
    "none_",
    "or_",
]
