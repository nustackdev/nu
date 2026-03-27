"""PV-specific morphisms — unsafe primitive ops for PV substrate.

These morphisms call _unsafe_primitive_* methods on PV views
(UnsafePrimitiveOpsBase). They are PV-specific because not all
substrates expose these raw storage operations.

All named explicitly Unsafe — these are optimization internals for
tree deformers, not user-facing APIs.

Item morphisms:
    InitCmd                              — materialize container chain via fetch()
    ItemPrimitiveGetUnsafeOp             — _unsafe_primitive_read()
    ItemPrimitiveSetUnsafeCmd            — _unsafe_primitive_write(ensure_exists=True)
    ItemPrimitiveSetUnsafeParentSkipCmd  — _unsafe_primitive_write() (full skip)
    ItemPrimitiveDeleteUnsafeCmd         — _unsafe_primitive_delete()

Collection morphisms:
    ScanPrimitivesUnsafeOp               — _unsafe_primitive_scan_values()
    ClearPrimitivesUnsafeCmd             — _unsafe_primitive_clear()
"""

from .collection import (
    ClearPrimitivesUnsafeCmd,
    ScanPrimitivesUnsafeOp,
)
from .item import (
    EnsureLayoutCmd,
    InitCmd,
    ItemPrimitiveDeleteUnsafeCmd,
    ItemPrimitiveGetUnsafeOp,
    ItemPrimitiveSetUnsafeCmd,
    ItemPrimitiveSetUnsafeParentSkipCmd,
)


__all__ = [
    "ClearPrimitivesUnsafeCmd",
    "EnsureLayoutCmd",
    "InitCmd",
    "ItemPrimitiveDeleteUnsafeCmd",
    "ItemPrimitiveGetUnsafeOp",
    "ItemPrimitiveSetUnsafeCmd",
    "ItemPrimitiveSetUnsafeParentSkipCmd",
    "ScanPrimitivesUnsafeOp",
]
