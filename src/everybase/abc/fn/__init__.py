"""User-facing functional operations.

Typed Value-returning factories over morphism Ops.
Morphisms own the computation; fn/ owns the typed composition layer.

Usage::

    from everybase.abc import fn

    fn.Map(items, str.upper)
    fn.Take(items, 5).to_list()
    fn.Len(my_dict)
    fn.ToInt(some_str) + 1
"""

from __future__ import annotations

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
    # Itertools
    "All",
    "Any",
    "Chain",
    # Builtins
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
    # Conversions
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
