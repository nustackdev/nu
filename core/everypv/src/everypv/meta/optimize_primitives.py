"""optimize_primitives — replace standard morphisms with unsafe PV-native ops.

optimize_primitive_reads:  ItemGetOp → ItemPrimitiveGetUnsafeOp
optimize_primitive_writes: ItemSetCmd → ItemPrimitiveSetUnsafeCmd
"""

from __future__ import annotations

from everybase import Node, replace
from everypv.meta.flat_ref import FlatRef as PVFlatRef
from everypv.morphisms.item import ItemPrimitiveGetUnsafeOp, ItemPrimitiveSetUnsafeCmd
from everyshape.morphisms.item import ItemGetOp, ItemSetCmd


__all__ = [
    "optimize_primitive_reads",
    "optimize_primitive_writes",
]


def _is_pv_ref(node: object) -> bool:
    """Check if a morphism node holds a PV substrate ref."""
    ref = getattr(node, "ref", None)
    return isinstance(ref, PVFlatRef)


def optimize_primitive_reads[N: Node](tree: N) -> N:
    """ItemGetOp → ItemPrimitiveGetUnsafeOp (PV refs only)."""
    return replace(
        tree,
        lambda n: isinstance(n, ItemGetOp) and _is_pv_ref(n),
        lambda n: ItemPrimitiveGetUnsafeOp(n.ref),
    )


def optimize_primitive_writes[N: Node](tree: N) -> N:
    """ItemSetCmd → ItemPrimitiveSetUnsafeCmd (PV refs only)."""
    return replace(
        tree,
        lambda n: isinstance(n, ItemSetCmd) and _is_pv_ref(n),
        lambda n: ItemPrimitiveSetUnsafeCmd(n.ref, n.value_expr),
    )
