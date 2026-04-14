"""auto_atomic - wrap unwrapped fabric interactions.

Three rules:
1. Op with WRITE override + Ref at that position -> Transaction(Op)
2. Op with READ override + Ref at that position -> Snapshot(Op)
3. Bare Ref -> Snapshot(Ref)

Recurses top-down. Skips existing Transaction/Snapshot/Atomic.
Rules 1-2 don't recurse inside (the boundary covers the subtree).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu import Nu
from nu.terms.effect import Direction, tracked_effects
from nu.terms.op import Op
from nu.terms.ref import Ref

from ..ops.control import Atomic, Snapshot, Transaction


if TYPE_CHECKING:
    from collections.abc import Hashable


__all__ = [
    "auto_atomic",
]


def _has_pv_write(node: Nu) -> bool:
    """Check if subtree has any WRITE effects. Used by Atomic."""
    return any(
        Direction.WRITE in e.direction
        for e in tracked_effects(node)
    )


def _override_direction(op: Op) -> Direction | None:
    """Check if Op has overrides with Ref at override positions.

    Returns the combined direction, or None if no overrides match.
    """
    overrides = op.overrides
    if not overrides:
        return None
    result = Direction(0)
    for i, direction in overrides.items():
        if i < len(op.children) and isinstance(op.children[i], Ref):
            result |= direction
    return result if result else None


def _walk(tree: Nu, scope: Hashable | None = None) -> Nu:
    """Walk the tree, apply the rules."""
    # Skip existing boundaries
    if isinstance(tree, (Transaction, Snapshot, Atomic)):
        return tree

    kwargs: dict = {}
    if scope is not None:
        kwargs["scope"] = scope

    # Rules 1-2: Op with overrides + Ref -> wrap the Op
    if isinstance(tree, Op):
        direction = _override_direction(tree)
        if direction is not None:
            if Direction.WRITE in direction:
                return Transaction(tree, **kwargs)
            return Snapshot(tree, **kwargs)

    # Rule 3: bare Ref -> Snapshot(Ref)
    if isinstance(tree, Ref):
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
    """Wrap unwrapped fabric interactions.

    WRITE override Ops get Transaction. READ override Ops get Snapshot.
    Bare Refs get Snapshot. Everything else is recursed.
    Existing boundaries are respected.

    Args:
        tree: Tree to rewrite.
        scope: Optional scope tag for Transaction/Snapshot.

    Returns:
        New tree with Transaction/Snapshot injected.
    """
    return _walk(tree, scope)
