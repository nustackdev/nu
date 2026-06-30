"""optimize_primitives — replace standard ops with unsafe virtuals-native ops.

optimize_primitive_reads:  ItemLoad → ItemPrimitiveGetUnsafe
optimize_primitive_writes: ItemStoreCmd → ItemPrimitiveSetUnsafeCmd
"""

from __future__ import annotations

from nu import Nu, replace
from nu.shapes.commands.item import ItemStoreCmd
from nu.shapes.queries.item import ItemLoad
from nu_virtuals.commands.item import ItemPrimitiveSetUnsafeCmd
from nu_virtuals.queries.item import ItemPrimitiveGetUnsafe
from nu_virtuals.refs.flat import FlatRef


__all__ = [
    "optimize_primitive_reads",
    "optimize_primitive_writes",
]


def _is_substrate_ref(node: object) -> bool:
    """Check if an op node holds a virtuals substrate ref."""
    ref = getattr(node, "ref", None)
    return isinstance(ref, FlatRef)


def optimize_primitive_reads[N: Nu](tree: N) -> N:
    """ItemLoad → ItemPrimitiveGetUnsafe (virtuals refs only)."""
    return replace(
        tree,
        lambda n: isinstance(n, ItemLoad) and _is_substrate_ref(n),
        lambda n: ItemPrimitiveGetUnsafe(n.ref),
    )


def optimize_primitive_writes[N: Nu](tree: N) -> N:
    """ItemStoreCmd → ItemPrimitiveSetUnsafeCmd (virtuals refs only)."""
    return replace(
        tree,
        lambda n: isinstance(n, ItemStoreCmd) and _is_substrate_ref(n),
        lambda n: ItemPrimitiveSetUnsafeCmd(n.ref, n.value_expr),
    )
