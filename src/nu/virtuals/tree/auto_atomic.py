"""auto_atomic - wrap unwrapped virtuals fabric interactions.

Two rules (applied to virtuals fabric refs — ViewRef/PrimitiveRef/FlatRef):
1. Op with a WRITE position holding a virtuals Ref -> Transaction(Op)
2. Bare virtuals Ref -> Snapshot(Ref)

Non-virtuals Refs (other fabrics) are left unwrapped — they have their own
boundary mechanisms.

Recurses top-down. Skips existing Transaction/Snapshot only when their scope
matches the current scope. Boundaries with a different scope are recursed into.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..interactions.atomicity import Snapshot, Transaction
from ..refs.base import PrimitiveRef, ViewRef
from ..refs.flat import FlatRef


# Refs that belong to the virtuals fabric and need atomic wrapping.
_VirtualsRef = (ViewRef, PrimitiveRef, FlatRef)


if TYPE_CHECKING:
    from collections.abc import Hashable

    from nu import Nu


__all__ = [
    "auto_atomic",
]


def _write_positions(op: object) -> tuple[int, ...]:
    """Return declared WRITE child positions on the op via its ``mutates`` attr."""
    attrs = getattr(type(op), "attributes", None)
    if not attrs or "mutates" not in attrs:
        return ()
    value = attrs["mutates"].value
    positions = value if isinstance(value, (frozenset, set)) else {value}
    return tuple(sorted(positions))


def _has_write_ref(op: Nu) -> bool:
    """Check if the op has a WRITE position holding a virtuals Ref."""
    children = op.children
    return any(
        i < len(children) and isinstance(children[i], _VirtualsRef)
        for i in _write_positions(op)
    )


def _find_write_ref(op: Nu) -> ViewRef | PrimitiveRef | FlatRef | None:
    """Find the first WRITE-position virtuals Ref in an op."""
    children = op.children
    for i in _write_positions(op):
        if i < len(children) and isinstance(children[i], _VirtualsRef):
            return children[i]
    return None


def _ref_matches_scope(ref: ViewRef | PrimitiveRef | FlatRef, scope: Hashable) -> bool:
    """Check if a virtuals ref belongs to the given root shape."""
    return ref.get_root_shape() is scope


def _covers(enclosing_scopes: tuple, ref_scope: Hashable) -> bool:
    """Check if any enclosing boundary already covers a ref with this root shape."""
    return any(s is None or s is ref_scope for s in enclosing_scopes)


def _is_leaf(node: object) -> bool:
    return not getattr(node, "children", ())


def _walk(tree: Nu, scope: Hashable | None, enclosing: tuple) -> Nu:
    """Walk the tree, apply the rules."""
    # Skip existing boundaries whose scope matches ours (identical wrap).
    if isinstance(tree, (Transaction, Snapshot)):
        if tree.scope is scope:
            return tree
        child_enclosing = (*enclosing, tree.scope)
        if not tree.children:
            return tree
        new_children = []
        changed = False
        for child in tree.children:
            new_child = _walk(child, scope, child_enclosing)
            new_children.append(new_child)
            if new_child is not child:
                changed = True
        if not changed:
            return tree
        return tree.with_children(*new_children)

    kwargs: dict = {}
    if scope is not None:
        kwargs["scope"] = scope

    # Rule 1: Op with WRITE position + virtuals Ref -> Transaction(Op)
    if _write_positions(tree):
        if scope is not None:
            write_ref = _find_write_ref(tree)
            if (
                write_ref is not None
                and _ref_matches_scope(write_ref, scope)
                and not _covers(enclosing, scope)
            ):
                return Transaction(tree, **kwargs)
        elif _has_write_ref(tree):
            write_ref = _find_write_ref(tree)
            ref_root = write_ref.get_root_shape() if write_ref is not None else None
            if not _covers(enclosing, ref_root):
                return Transaction(tree, **kwargs)

    # Rule 2: bare virtuals Ref -> Snapshot(Ref)
    if isinstance(tree, _VirtualsRef):
        if scope is not None:
            if _ref_matches_scope(tree, scope) and not _covers(enclosing, scope):
                return Snapshot(tree, **kwargs)
        else:
            ref_root = tree.get_root_shape()
            if not _covers(enclosing, ref_root):
                return Snapshot(tree, **kwargs)

    # Recurse
    if not tree.children:
        return tree

    new_children = []
    changed = False
    for child in tree.children:
        new_child = _walk(child, scope, enclosing)
        new_children.append(new_child)
        if new_child is not child:
            changed = True

    if not changed:
        return tree
    return tree.with_children(*new_children)


def auto_atomic(tree: Nu, scope: Hashable | None = None) -> Nu:
    """Wrap unwrapped virtuals fabric interactions.

    WRITE-effect ops with virtuals Refs get Transaction. Bare virtuals Refs get
    Snapshot. Non-virtuals Refs are left unwrapped. Existing boundaries are
    respected.

    When scope is None (default): wraps all unwrapped virtuals refs without a
    scope tag. When scope is set: only wraps refs whose root_shape matches scope,
    tagging the boundary with that scope.
    """
    return _walk(tree, scope, ())
