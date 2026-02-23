"""optimize_primitives — replace standard morphisms with unsafe PV-native ops.

optimize_primitive_reads:  ItemGetOp → ItemPrimitiveGetUnsafeOp
optimize_primitive_writes: ItemSetCmd → ItemPrimitiveSetUnsafeCmd
"""

from __future__ import annotations

from everybase import Node, replace
from everypv.morphisms.item import ItemPrimitiveGetUnsafeOp, ItemPrimitiveSetUnsafeCmd
from everyshape.morphisms.item import ItemGetOp, ItemSetCmd


__all__ = [
    "optimize_primitive_reads",
    "optimize_primitive_writes",
]


def optimize_primitive_reads[N: Node](tree: N) -> N:
    """ItemGetOp → ItemPrimitiveGetUnsafeOp."""
    return replace(
        tree,
        lambda n: isinstance(n, ItemGetOp),
        lambda n: ItemPrimitiveGetUnsafeOp(n.ref),
    )


def optimize_primitive_writes[N: Node](tree: N) -> N:
    """ItemSetCmd → ItemPrimitiveSetUnsafeCmd."""
    return replace(
        tree,
        lambda n: isinstance(n, ItemSetCmd),
        lambda n: ItemPrimitiveSetUnsafeCmd(n.ref, n.value_expr),
    )
