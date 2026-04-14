"""auto_atomic - Wrap Nu subtrees in Transaction/Snapshot using effect analysis.

Walks the tree, computes tracked effects per subtree, wraps with the
minimum boundary needed:
    READ + WRITE on same fabric -> Transaction
    WRITE only -> Transaction (virtuals has no WriteBatch yet)
    READ only -> Snapshot

Two granularity levels:
    "nu" (default): at each bare Nu node, analyze and wrap each child independently.
    "op": recurse into all branches, wrap at the finest fabric-touching Op level.

Existing Transaction/Snapshot ops (placed by user) are respected and not re-wrapped.
"""

from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING, Literal

from nu import Nu
from nu.terms.effect import Direction, TrackedEffect, tracked_effects
from nu.terms.ref import Ref

from ..ops.control import Snapshot, Transaction


if TYPE_CHECKING:
    from collections.abc import Hashable


__all__ = [
    "auto_atomic",
]


def _effects_by_fabric(
    effects: frozenset[TrackedEffect],
) -> dict[type, Direction]:
    """Group tracked effects by fabric, union directions."""
    by_fabric: dict[type, Direction] = defaultdict(lambda: Direction(0))
    for e in effects:
        by_fabric[e.fabric] |= e.direction
    return dict(by_fabric)


def _needs_wrapping(node: Nu) -> bool:
    """Check if a node's subtree has any fabric effects."""
    return len(tracked_effects(node)) > 0


def _has_write(node: Nu, fabric: type | None = None) -> bool:
    """Check if subtree has WRITE effects, optionally filtered by fabric."""
    for e in tracked_effects(node):
        if Direction.WRITE in e.direction:
            if fabric is None or e.fabric is fabric:
                return True
    return False


def _wrap(node: Nu, scope: Hashable | None = None) -> Nu:
    """Wrap a node in Transaction or Snapshot based on its effects."""
    kwargs: dict = {}
    if scope is not None:
        kwargs["scope"] = scope

    if _has_write(node):
        return Transaction(node, **kwargs)
    return Snapshot(node, **kwargs)


def _auto_atomic_nu(tree: Nu, scope: Hashable | None = None) -> Nu:
    """Per-Nu granularity: at each bare Nu, wrap children independently."""
    # Skip existing Transaction/Snapshot
    if isinstance(tree, (Transaction, Snapshot)):
        return tree

    # Bare Nu (sequencing node from a | b) - wrap each child independently
    if type(tree) is Nu:
        new_children = []
        for child in tree.children:
            if isinstance(child, (Transaction, Snapshot)):
                new_children.append(child)
            elif _needs_wrapping(child):
                new_children.append(_wrap(child, scope))
            else:
                # Recurse into non-fabric children to find bare Nus deeper
                new_children.append(_auto_atomic_nu(child, scope))
        return tree.with_children(*new_children)

    # Other nodes: recurse into children
    if tree.is_leaf:
        return tree

    new_children = []
    changed = False
    for child in tree.children:
        new_child = _auto_atomic_nu(child, scope)
        new_children.append(new_child)
        if new_child is not child:
            changed = True

    if not changed:
        return tree
    return tree.with_children(*new_children)


def _auto_atomic_op(tree: Nu, scope: Hashable | None = None) -> Nu:
    """Per-Op granularity: recurse deep, wrap at the leaf-most fabric Ops.

    Bottom-up: recurse all the way down first, then wrap Ops that directly
    touch fabric (have overrides with Ref children). Parent nodes are left
    unwrapped because their children are already covered.
    """
    # Skip existing Transaction/Snapshot
    if isinstance(tree, (Transaction, Snapshot)):
        return tree

    if tree.is_leaf:
        return tree

    # First: recurse into all children (go deep)
    new_children = []
    changed = False
    for child in tree.children:
        if isinstance(child, (Transaction, Snapshot)):
            new_children.append(child)
            continue
        new_child = _auto_atomic_op(child, scope)
        # After recursion, if this child is a fabric Op (has overrides with Refs),
        # wrap it. This is the leaf-most wrapping point.
        overrides = getattr(new_child, "overrides", {})
        if overrides and any(
            isinstance(new_child.children[i], Ref)
            for i in overrides
            if i < len(new_child.children)
        ):
            new_child = _wrap(new_child, scope)
        new_children.append(new_child)
        if new_child is not child:
            changed = True

    if not changed:
        return tree
    return tree.with_children(*new_children)


def auto_atomic(
    tree: Nu,
    scope: Hashable | None = None,
    granularity: Literal["nu", "op"] = "nu",
) -> Nu:
    """Wrap subtrees in Transaction/Snapshot based on effect analysis.

    Walks the tree, computes effects, inserts minimum boundaries.
    Existing Transaction/Snapshot ops are respected.

    Args:
        tree: Tree to rewrite.
        scope: Optional scope tag for Transaction/Snapshot.
        granularity: "nu" (default) wraps at bare Nu children level.
                     "op" wraps at individual fabric Op level.

    Returns:
        New tree with Transaction/Snapshot injected.
    """
    if granularity == "op":
        return _auto_atomic_op(tree, scope)
    return _auto_atomic_nu(tree, scope)
