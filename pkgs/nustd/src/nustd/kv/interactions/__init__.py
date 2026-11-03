"""Virtuals interactions, split by domain (item / collections / atomicity).

- ``item``: leaf-level unsafe primitive read/write/delete + container setup
  (load + store optimization internals for tree deformers).
- ``collections``: container-level unsafe scan / clear.
- ``kh57``: sampled and whole reads of an int-keyed range.
- ``ordered``: placement, moves and ends of an ordered dict.
- ``atomicity``: snapshot / transaction brackets + conflict-aware retry.
"""

from .atomicity import (
    CONFLICT_ERRORS,
    Atomic,
    RetryOnConflict,
    Snapshot,
    Transaction,
    _has_virtuals_write,
)
from .collections import ClearPrimitivesUnsafeCmd, ScanPrimitivesUnsafe
from .item import (
    InitItemCmd,
    ItemPrimitiveDeleteUnsafeCmd,
    ItemPrimitiveGetUnsafe,
    ItemPrimitiveSetCmd,
    ItemPrimitiveSetUnsafeCmd,
    ItemPrimitiveSetUnsafeParentSkipCmd,
)
from .kh57 import Kh57Range, Kh57Sample
from .ordered import (
    OrderedFirst,
    OrderedInsertAfterCmd,
    OrderedInsertBeforeCmd,
    OrderedLast,
    OrderedMoveCmd,
)


__all__ = [
    "CONFLICT_ERRORS",
    "Atomic",
    "ClearPrimitivesUnsafeCmd",
    "InitItemCmd",
    "ItemPrimitiveDeleteUnsafeCmd",
    "ItemPrimitiveGetUnsafe",
    "ItemPrimitiveSetCmd",
    "ItemPrimitiveSetUnsafeCmd",
    "ItemPrimitiveSetUnsafeParentSkipCmd",
    "Kh57Range",
    "Kh57Sample",
    "OrderedFirst",
    "OrderedInsertAfterCmd",
    "OrderedInsertBeforeCmd",
    "OrderedLast",
    "OrderedMoveCmd",
    "RetryOnConflict",
    "ScanPrimitivesUnsafe",
    "Snapshot",
    "Transaction",
    "_has_virtuals_write",
]
