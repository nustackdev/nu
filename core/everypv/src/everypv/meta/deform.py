"""PV deformations — semantics-preserving tree transforms for PV optimization.

deform_reads:  Value(ItemGetOp) → ItemPrimitiveGetUnsafeOp
deform_writes: Value(ItemSetCmd) → ItemPrimitiveSetUnsafeCmd
"""

from __future__ import annotations

from everybase import Node, Value, replace
from everypv.morphisms.item import ItemPrimitiveGetUnsafeOp, ItemPrimitiveSetUnsafeCmd
from everyshape.morphisms.item import ItemGetOp, ItemSetCmd


__all__ = [
    "deform_reads",
    "deform_writes",
]


def deform_reads[N: Node](tree: N) -> N:
    """Value(ItemGetOp) → ItemPrimitiveGetUnsafeOp."""
    return replace(
        tree,
        lambda n: isinstance(n, Value)
        and n.child_count == 1
        and isinstance(n.children[0], ItemGetOp),
        lambda n: ItemPrimitiveGetUnsafeOp(n.children[0].ref),
    )


def deform_writes[N: Node](tree: N) -> N:
    """Value(ItemSetCmd) → ItemPrimitiveSetUnsafeCmd."""
    return replace(
        tree,
        lambda n: isinstance(n, Value)
        and n.child_count == 1
        and isinstance(n.children[0], ItemSetCmd),
        lambda n: ItemPrimitiveSetUnsafeCmd(n.children[0].ref, n.children[0].value_expr),
    )
