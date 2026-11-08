"""Virtuals interactions, split by domain (item / collections / atomicity).

- ``item``: leaf-level unsafe primitive read/write/delete + container setup
  (load + store optimization internals for tree deformers).
- ``collections``: container-level unsafe scan / clear.
- ``kh57``: sampled and whole reads of an int-keyed range.
- ``ordered``: placement, moves and ends of an ordered dict.
- ``paging``: a page of a mapping's keys from a cursor, and its two ends.
- ``ring``: a page of a ring's entries past a sequence number.
- ``extract``: whole-container read, NULL where nothing is written.
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
from .extract import ViewExtract
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
from .paging import FirstKey, KeysPage, LastKey, ReversedKeysPage
from .ring import RingEntries


__all__ = [
    "CONFLICT_ERRORS",
    "Atomic",
    "ClearPrimitivesUnsafeCmd",
    "FirstKey",
    "InitItemCmd",
    "ItemPrimitiveDeleteUnsafeCmd",
    "ItemPrimitiveGetUnsafe",
    "ItemPrimitiveSetCmd",
    "ItemPrimitiveSetUnsafeCmd",
    "ItemPrimitiveSetUnsafeParentSkipCmd",
    "KeysPage",
    "Kh57Range",
    "Kh57Sample",
    "LastKey",
    "OrderedFirst",
    "OrderedInsertAfterCmd",
    "OrderedInsertBeforeCmd",
    "OrderedLast",
    "OrderedMoveCmd",
    "RetryOnConflict",
    "ReversedKeysPage",
    "RingEntries",
    "ScanPrimitivesUnsafe",
    "Snapshot",
    "Transaction",
    "ViewExtract",
    "_has_virtuals_write",
]
