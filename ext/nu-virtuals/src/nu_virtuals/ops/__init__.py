"""PV-specific ops - unsafe primitive ops for PV substrate.

These ops call _unsafe_primitive_* methods on PV views
(UnsafePrimitiveOpsBase). They are PV-specific because not all
substrates expose these raw storage operations.

All named explicitly Unsafe - these are optimization internals for
tree deformers, not user-facing APIs.

Item ops:
    InitCmd                              - materialize container chain via fetch()
    ItemPrimitiveGetUnsafeOp             - _unsafe_primitive_read()
    ItemPrimitiveSetUnsafeCmd            - _unsafe_primitive_write(ensure_exists=True)
    ItemPrimitiveSetUnsafeParentSkipCmd  - _unsafe_primitive_write() (full skip)
    ItemPrimitiveDeleteUnsafeCmd         - _unsafe_primitive_delete()

Collection ops:
    PrimitiveStoreCmd                    - _primitive_write() (blob store for compound primitives)
    ScanPrimitivesUnsafeOp               - _unsafe_primitive_scan_values()
    ClearPrimitivesUnsafeCmd             - _unsafe_primitive_clear()

Control ops:
    AtomicScope                               - transaction/snapshot boundary (auto-selects)
    Snapshot                             - read-only snapshot boundary
    Transaction                          - write transaction boundary
"""

from .collection import (
    ClearPrimitivesUnsafeCmd,
    ScanPrimitivesUnsafeOp,
)
from .control import AtomicScope, Snapshot, Transaction
from .item import (
    EnsureLayoutCmd,
    InitCmd,
    ItemPrimitiveDeleteUnsafeCmd,
    ItemPrimitiveGetUnsafeOp,
    ItemPrimitiveSetUnsafeCmd,
    ItemPrimitiveSetUnsafeParentSkipCmd,
    PrimitiveStoreCmd,
)


__all__ = [
    "AtomicScope",
    "ClearPrimitivesUnsafeCmd",
    "EnsureLayoutCmd",
    "InitCmd",
    "ItemPrimitiveDeleteUnsafeCmd",
    "ItemPrimitiveGetUnsafeOp",
    "ItemPrimitiveSetUnsafeCmd",
    "ItemPrimitiveSetUnsafeParentSkipCmd",
    "PrimitiveStoreCmd",
    "ScanPrimitivesUnsafeOp",
    "Snapshot",
    "Transaction",
]
