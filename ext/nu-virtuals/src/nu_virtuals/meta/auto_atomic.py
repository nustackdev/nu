"""auto_atomic - wrap unwrapped virtuals fabric interactions.

Two rules (applied to shapes Refs and FlatRefs, i.e. virtuals fabric refs):
1. Interaction with WRITE override + virtuals Ref at that position -> Transaction(Interaction)
2. Bare virtuals Ref -> Snapshot(Ref)

Non-virtuals Refs (StdioRef, AttrRef, ServiceRef) are left unwrapped.
They belong to different fabrics with their own boundary mechanisms.

Recurses top-down. Skips existing Transaction/Snapshot/AtomicScope only when their
scope matches the current scope. Boundaries with a different scope are recursed
into - they don't cover refs belonging to our scope.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.shapes.refs.base import Ref as ShapesRef
from nu.terms import Direction, Interaction, tracked_effects

from ..meta.flat_ref import FlatRef
from ..ops.control import AtomicScope, Snapshot, Transaction


# Refs that belong to the virtuals fabric and need atomic wrapping.
# After inline_refs: virtuals refs are FlatRef, nu_dict refs are gone.
# ShapesRef catches non-inlined virtuals refs (e.g. cross-fabric dynamic keys).
_VirtualsRef = (ShapesRef, FlatRef)


if TYPE_CHECKING:
    from collections.abc import Hashable

    from nu import Nu


__all__ = [
    "auto_atomic",
]


def _has_pv_write(node: Nu) -> bool:
    """Check if subtree has any WRITE effects. Used by AtomicScope."""
    return any(Direction.WRITE in e.direction for e in tracked_effects(node))


def _write_positions(op: Interaction) -> tuple[int, ...]:
    """Return WRITE child positions declared on the Interaction."""
    spec = op.writes
    if isinstance(spec, int):
        return (spec,)
    return tuple(spec)


def _has_write_ref(op: Interaction) -> bool:
    """Check if Interaction has a WRITE position with a virtuals Ref at that position."""
    for i in _write_positions(op):
        if i < len(op.children) and isinstance(op.children[i], _VirtualsRef):
            return True
    return False


def _find_write_ref(op: Interaction) -> ShapesRef | FlatRef | None:
    """Find the first WRITE-position virtuals Ref in an Interaction."""
    for i in _write_positions(op):
        if i < len(op.children) and isinstance(op.children[i], _VirtualsRef):
            return op.children[i]
    return None


def _ref_matches_scope(ref: ShapesRef | FlatRef, scope: Hashable) -> bool:
    """Check if a virtuals ref belongs to the given root shape."""
    return ref.get_root_shape() is scope


def _covers(enclosing_scopes: tuple, ref_scope: Hashable) -> bool:
    """Check if any enclosing boundary already covers a ref with root_shape=ref_scope.

    A boundary covers a ref when:
    - boundary scope is None (unscoped boundary covers everything), OR
    - boundary scope is the ref's root shape (scoped boundary covers matching refs).

    ``enclosing_scopes`` is a tuple of scope values from Transaction/AtomicScope/Snapshot
    ancestors already seen on the walk path. Sentinel ``_UNSET`` means "no ancestor".
    """
    for s in enclosing_scopes:
        if s is None or s is ref_scope:
            return True
    return False


def _walk(tree: Nu, scope: Hashable | None, enclosing: tuple) -> Nu:
    """Walk the tree, apply the rules.

    When scope is None: wrap all unwrapped virtuals refs (no scope tag).
    When scope is set: only wrap refs whose root_shape matches scope,
    tagging the boundary with that scope. Other refs are left unwrapped.

    ``enclosing`` is a tuple of scope values of Transaction/AtomicScope/Snapshot
    ancestors already passed through. Used to skip redundant wrapping when
    an ancestor boundary already covers the ref(s) we'd wrap.
    """
    # Skip existing boundaries whose scope matches ours (identical wrap).
    # For non-matching scope, still recurse but register this boundary as
    # enclosing so nested rules can see it already covers compatible refs.
    if isinstance(tree, (Transaction, Snapshot, AtomicScope)):
        if tree.scope is scope:
            return tree
        child_enclosing = enclosing + (tree.scope,)
        if tree._is_leaf:
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
        return tree._with_children(*new_children)

    kwargs: dict = {}
    if scope is not None:
        kwargs["scope"] = scope

    # Rule 1: Interaction with WRITE position + virtuals Ref -> Transaction(Interaction)
    if isinstance(tree, Interaction) and _write_positions(tree):
        if scope is not None:
            # Scoped: only wrap if the write ref matches this scope
            write_ref = _find_write_ref(tree)
            if write_ref is not None and _ref_matches_scope(write_ref, scope):
                # Skip if an enclosing boundary already covers this scope.
                if _covers(enclosing, scope):
                    pass  # fall through to recurse
                else:
                    return Transaction(tree, **kwargs)
        elif _has_write_ref(tree):
            write_ref = _find_write_ref(tree)
            ref_root = write_ref.get_root_shape() if write_ref is not None else None
            if _covers(enclosing, ref_root):
                pass  # already covered, fall through to recurse
            else:
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
    if tree._is_leaf:
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
    return tree._with_children(*new_children)


def auto_atomic(tree: Nu, scope: Hashable | None = None) -> Nu:
    """Wrap unwrapped virtuals fabric interactions.

    WRITE override Ops with virtuals Refs get Transaction.
    Bare virtuals Refs get Snapshot. Non-virtuals Refs (StdioRef, etc.)
    are left unwrapped. Existing boundaries are respected.

    When scope is None (default): wraps all unwrapped virtuals refs
    without a scope tag (uses default navigator).

    When scope is set: only wraps refs whose root_shape matches scope,
    tagging the boundary with that scope. Use this to target a specific
    shape root for a separate navigator binding. Call multiple times
    with different scopes for multi-navigator setups::

        tree = auto_atomic(tree, scope=LedgerShard)  # shard refs first
        tree = auto_atomic(tree)                       # remaining refs

    Args:
        tree: Tree to rewrite.
        scope: Shape root to filter and tag. None = wrap all.

    Returns:
        New tree with Transaction/Snapshot injected.
    """
    return _walk(tree, scope, ())
