"""annotate_ref_loads - wrap bare Refs with load ops for optimizer matching.

When Refs are used directly as Nu children (e.g. ref + 1), the tree
contains bare Ref nodes. Substrate optimizers (like PV's optimize_primitive_reads)
match on ItemLoadOp/CollectionLoadOp nodes to replace them with fast-path ops.

This pass walks the tree and wraps bare Refs that appear in value positions
with the appropriate load op, giving optimizers something to match on.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.tree import map_nodes


if TYPE_CHECKING:
    from nu.terms import Nu


__all__ = [
    "annotate_ref_loads",
]


def annotate_ref_loads(root: Nu) -> Nu:
    """Wrap bare Refs with load ops for optimizer matching.

    Walks the tree bottom-up. For each non-leaf node, wraps any child
    that is a shape Ref (and not already the target of an op) with
    the appropriate load op (ItemLoadOp for item refs, CollectionLoadOp
    for collection refs).

    This is idempotent - already-wrapped refs are not double-wrapped.
    """
    from nu.shapes.collections import ItemI
    from nu.shapes.ops import CollectionLoadOp
    from nu.shapes.ops import ItemLoadOp
    from nu.shapes.refs import Ref as ShapeRef

    load_op_types = (ItemLoadOp, CollectionLoadOp)

    def _process(node: Nu) -> Nu:
        if node.is_leaf:
            return node

        if isinstance(node, load_op_types):
            return node

        target_ref = getattr(node, "ref", None)
        new_children: list[Nu] = []
        changed = False

        for child in node.children:
            if child is target_ref:
                new_children.append(child)
                continue

            if isinstance(child, ShapeRef) and not isinstance(child, load_op_types):
                if isinstance(child, ItemI):
                    new_children.append(ItemLoadOp(child))
                else:
                    new_children.append(CollectionLoadOp(child))
                changed = True
            else:
                new_children.append(child)

        if changed:
            return node.with_children(*new_children)
        return node

    return map_nodes(root, _process, order="bottom_up")
