"""Reference operations module.

Re-exports from:
- access: Core access operations (GetOp, ExtractOp, etc.)
- query: Mapping query operations (KeysOp, ValuesOp, etc.)
- functional: Higher-order/functional operations (MapOp, FilterOp, etc.)
- search: Search operations (IndexOp, CountOp, FindOp, etc.)
"""

from .access import (
    ExistsOp,
    ExtractOp,
    GetOp,
    LengthOp,
    MissingOp,
)
from .functional import (
    FilterItemsOp,
    FilterOp,
    MapItemsOp,
    MapOp,
    MapValuesOp,
    ReduceItemsOp,
    ReduceOp,
)
from .query import (
    ItemsOp,
    KeysOp,
    MappingGetOp,
    ValuesOp,
)
from .search import (
    CountOp,
    FindIndexOp,
    FindItemOp,
    FindKeyOp,
    FindOp,
    FindValueOp,
    IndexOp,
)


__all__ = [
    "CountOp",
    "ExistsOp",
    "ExtractOp",
    "FilterItemsOp",
    "FilterOp",
    "FindIndexOp",
    "FindItemOp",
    "FindKeyOp",
    "FindOp",
    "FindValueOp",
    # Access ops
    "GetOp",
    # Search ops
    "IndexOp",
    "ItemsOp",
    # Query ops
    "KeysOp",
    "LengthOp",
    "MapItemsOp",
    # Functional ops
    "MapOp",
    "MapValuesOp",
    "MappingGetOp",
    "MissingOp",
    "ReduceItemsOp",
    "ReduceOp",
    "ValuesOp",
]
