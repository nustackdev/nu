"""auto_atomic - wrap unwrapped virtuals fabric interactions.

Two rules (applied only to shapes Refs, i.e. document-model refs):
1. Op with WRITE override + shapes Ref at that position -> Transaction(Op)
2. Bare shapes Ref -> Snapshot(Ref)

Non-shapes Refs (StdioRef, AttrRef, ServiceRef) are left unwrapped.
They belong to different fabrics with their own boundary mechanisms.

Recurses top-down. Skips existing Transaction/Snapshot/Atomic.
Rule 1 doesn't recurse inside (the boundary covers the subtree).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.shapes.refs.base import Ref as ShapesRef
from nu.terms.effect import Direction, tracked_effects
from nu.terms.op import Op

from ..ops.control import Atomic, Snapshot, Transaction


if TYPE_CHECKING:
    from collections.abc import Hashable

    from nu import Nu


__all__ = [
    "auto_atomic",
]


def _has_pv_write(node: Nu) -> bool:
    """Check if subtree has any WRITE effects. Used by Atomic."""
    return any(
        Direction.WRITE in e.direction
        for e in tracked_effects(node)
    )


def _has_write_ref(op: Op) -> bool:
    """Check if Op has a WRITE override with a shapes Ref at that position."""
    for i, direction in op.overrides.items():
        if Direction.WRITE in direction and i < len(op.children) and isinstance(op.children[i], ShapesRef):
            return True
    return False


def _walk(tree: Nu, scope: Hashable | None = None) -> Nu:
    """Walk the tree, apply the rules."""
    # Skip existing boundaries
    if isinstance(tree, (Transaction, Snapshot, Atomic)):
        return tree

    kwargs: dict = {}
    if scope is not None:
        kwargs["scope"] = scope

    # Rule 1: Op with WRITE override + shapes Ref -> Transaction(Op)
    if isinstance(tree, Op) and tree.overrides and _has_write_ref(tree):
        return Transaction(tree, **kwargs)

    # Rule 2: bare shapes Ref -> Snapshot(Ref)
    if isinstance(tree, ShapesRef):
        return Snapshot(tree, **kwargs)

    # Recurse
    if tree.is_leaf:
        return tree

    new_children = []
    changed = False
    for child in tree.children:
        new_child = _walk(child, scope)
        new_children.append(new_child)
        if new_child is not child:
            changed = True

    if not changed:
        return tree
    return tree.with_children(*new_children)


def auto_atomic(tree: Nu, scope: Hashable | None = None) -> Nu:
    """Wrap unwrapped virtuals fabric interactions.

    WRITE override Ops with shapes Refs get Transaction.
    Bare shapes Refs get Snapshot. Non-shapes Refs (StdioRef, etc.)
    are left unwrapped. Existing boundaries are respected.

    Args:
        tree: Tree to rewrite.
        scope: Optional scope tag for Transaction/Snapshot.

    Returns:
        New tree with Transaction/Snapshot injected.
    """
    return _walk(tree, scope)
