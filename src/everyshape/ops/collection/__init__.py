"""Generic collection operations.

These operations are reusable across sequence types (list, tuple, custom sequences).

Modules:
- access.py: AtOp, SliceOp, LenOp, ContainsOp
- aggregate.py: SumOp, MinOp, MaxOp, AnyOp, AllOp
- transform.py: MapOp, FilterOp, ReduceOp, SortedOp, ReversedOp
- search.py: FirstOp, LastOp, IndexOfOp, FindOp, FindIndexOp, CountOp, JoinOp
"""

from .access import AtOp, ContainsOp, LenOp, SliceOp
from .aggregate import AllOp, AnyOp, MaxOp, MinOp, SumOp
from .search import CountOp, FindIndexOp, FindOp, FirstOp, IndexOfOp, JoinOp, LastOp
from .transform import FilterOp, MapOp, ReduceOp, ReversedOp, SortedOp


__all__ = [  # noqa: RUF022
    # access
    "AtOp",
    "ContainsOp",
    "LenOp",
    "SliceOp",
    # aggregate
    "AllOp",
    "AnyOp",
    "MaxOp",
    "MinOp",
    "SumOp",
    # transform
    "FilterOp",
    "MapOp",
    "ReduceOp",
    "ReversedOp",
    "SortedOp",
    # search
    "CountOp",
    "FindIndexOp",
    "FindOp",
    "FirstOp",
    "IndexOfOp",
    "JoinOp",
    "LastOp",
]
