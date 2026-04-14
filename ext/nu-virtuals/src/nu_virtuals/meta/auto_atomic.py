"""auto_atomic - wrap fabric-touching Ops in Transaction/Snapshot.

Walks the tree top-down. An Op is fabric-touching if it has a Ref as an
immediate child. Ref child = READ by default; overrides can mark WRITE.
Wraps in Transaction (WRITE) or Snapshot (READ-only) based on tracked effects.

ScopedOp.execute() returns the last child's value, so wrapping preserves
return values (scalars, subscriptions, etc.).

ScopedOp.open() keeps the boundary alive, so ForEach/Fold can iterate
lazy views through a wrapped source (e.g. Snapshot(ListRef)).

ForEach/Fold are skipped (not wrapped themselves) but their children are
wrapped individually. They use open() on their source child at runtime.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu import Nu
from nu.ops.control.iteration import Fold, ForEach
from nu.terms.effect import Direction, tracked_effects
from nu.terms.op import Op
from nu.terms.ref import Ref

from ..ops.control import Atomic, Snapshot, Transaction


if TYPE_CHECKING:
    from collections.abc import Hashable


__all__ = [
    "auto_atomic",
]


def _is_fabric_touching(op: Op) -> bool:
    """Op has a Ref as an immediate child."""
    return any(isinstance(child, Ref) for child in op.children)


def _has_pv_write(node: Nu) -> bool:
    """Check if subtree has any WRITE effects. Used by Atomic."""
    return any(
        Direction.WRITE in e.direction
        for e in tracked_effects(node)
    )


def _wrap(node: Nu, scope: Hashable | None = None) -> Nu:
    """Wrap in Transaction (WRITE) or Snapshot (READ-only)."""
    kwargs: dict = {}
    if scope is not None:
        kwargs["scope"] = scope
    if _has_pv_write(node):
        return Transaction(node, **kwargs)
    return Snapshot(node, **kwargs)


def _walk(tree: Nu, scope: Hashable | None = None) -> Nu:
    """Top-down walk: wrap fabric-touching Ops, skip inside wrapped subtrees."""
    # Skip existing boundaries
    if isinstance(tree, (Transaction, Snapshot, Atomic)):
        return tree

    # ForEach/Fold: don't wrap (they use open() on source), but recurse children
    if isinstance(tree, (ForEach, Fold)):
        return _recurse(tree, scope)

    # Fabric-touching Op: wrap, don't recurse inside
    if isinstance(tree, Op) and _is_fabric_touching(tree):
        return _wrap(tree, scope)

    # Leaf: nothing to do
    if tree.is_leaf:
        return tree

    # Recurse into children
    return _recurse(tree, scope)


def _recurse(tree: Nu, scope: Hashable | None = None) -> Nu:
    """Recurse into children."""
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
    """Wrap every unwrapped fabric-touching Op in the minimum boundary.

    Fabric-touching = has Ref as immediate child.
    Ref child defaults to READ; overrides mark WRITE.
    Transaction for WRITE, Snapshot for READ-only.

    ScopedOp.execute() returns values, so wrapping is transparent.
    ForEach/Fold use open() on their source child for lazy iteration.

    Args:
        tree: Tree to rewrite.
        scope: Optional scope tag for Transaction/Snapshot.

    Returns:
        New tree with Transaction/Snapshot injected.
    """
    return _walk(tree, scope)
