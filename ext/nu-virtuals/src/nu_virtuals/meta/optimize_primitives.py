"""optimize_primitives — replace standard morphisms with unsafe virtuals-native ops.

optimize_primitive_reads:  ItemLoadOp → ItemPrimitiveGetUnsafeOp
optimize_primitive_writes: ItemStoreCmd → ItemPrimitiveSetUnsafeCmd
"""

from __future__ import annotations

from nu_virtuals.meta.flat_ref import FlatRef
from nu_virtuals.morphisms.item import ItemPrimitiveGetUnsafeOp, ItemPrimitiveSetUnsafeCmd
from nu import Node, replace
from nu.shape.morphisms.item import ItemLoadOp, ItemStoreCmd


__all__ = [
    "optimize_primitive_reads",
    "optimize_primitive_writes",
]


def _is_substrate_ref(node: object) -> bool:
    """Check if a morphism node holds a virtuals substrate ref."""
    ref = getattr(node, "ref", None)
    return isinstance(ref, FlatRef)


def optimize_primitive_reads[N: Node](tree: N) -> N:
    """ItemLoadOp → ItemPrimitiveGetUnsafeOp (virtuals refs only)."""
    return replace(
        tree,
        lambda n: isinstance(n, ItemLoadOp) and _is_substrate_ref(n),
        lambda n: ItemPrimitiveGetUnsafeOp(n.ref),
    )


def optimize_primitive_writes[N: Node](tree: N) -> N:
    """ItemStoreCmd → ItemPrimitiveSetUnsafeCmd (virtuals refs only)."""
    return replace(
        tree,
        lambda n: isinstance(n, ItemStoreCmd) and _is_substrate_ref(n),
        lambda n: ItemPrimitiveSetUnsafeCmd(n.ref, n.value_expr),
    )
