"""The pass that decides, per branch, where a storage boundary belongs.

Writing atomicity by hand means answering the same question at every branch of
a tree - does this touch storage, and does it write - and getting it wrong in
either direction: a missing bracket leaves a read with no snapshot to resolve
against, an over-broad one holds a transaction open across work that had no
business being inside it.

The question is answerable from the tree itself. A Ref names the storage it
reads, and a node declares which of its slots it mutates. So the pass reads
both and places the boundary at the smallest branch that needs it, which is
the direct child of a Flow rather than the Flow as a whole - sibling branches
of a Sequential get their own brackets and commit independently.

The rest of the file is the bookkeeping that makes the walk honest: which refs
an enclosing bracket already covers, which scope dominates which, and where
the walk must stop because it cannot see through a node.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.lang import Flow, Span
from nu.lang.attributes import Sort

from ..interactions.atomicity import Snapshot, Transaction
from ..refs.base import PrimitiveRef, ViewRef


if TYPE_CHECKING:
    from collections.abc import Hashable, Iterator

    from nu.lang import Nu


__all__ = ["auto_flow_atomic"]


_VirtualsRef = (ViewRef, PrimitiveRef)


def _declared_sort(node: object) -> Sort | None:
    """Read the node's declared sort off its class (pre-compile access)."""
    attrs = getattr(type(node), "_attributes", None)
    if not attrs:
        return None
    sort_attr = attrs.get("sort")
    return getattr(sort_attr, "value", None) if sort_attr is not None else None


def _is_dynamic(node: object) -> bool:
    return _declared_sort(node) is Sort.DYNAMIC


def _write_positions(node: object) -> frozenset[int]:
    attrs = getattr(type(node), "_attributes", None)
    if not attrs or "mutates" not in attrs:
        return frozenset()
    value = attrs["mutates"].value
    return value if isinstance(value, frozenset) else frozenset(value)


def _dominates(broader: Hashable | None, specific: Hashable | None) -> bool:
    """True iff ``broader`` covers everything ``specific`` refers to.

    ``broader`` is a brace scope or the pass scope; ``specific`` is a
    ref's root shape or the pass scope.

    A universal scope (``None``) dominates any specific scope; a concrete
    scope dominates only itself.
    """
    return broader is None or broader is specific


def _covered_by_enclosing(enclosing: tuple, ref_scope: Hashable) -> bool:
    return any(_dominates(s, ref_scope) for s in enclosing)


def _iter_uncovered(
    node: object,
    pass_scope: Hashable | None,
    enclosing: tuple,
    _top: bool = True,
) -> Iterator[tuple[object, bool]]:
    """Yield ``(ref, is_write)`` for uncovered virtuals refs in a subtree.

    Only refs the pass cares about, that no enclosing brace covers.

    Refs are classified WRITE iff they sit in a mutation slot of an
    enclosing op. A top-level Ref (a subtree that IS a Ref, e.g. the
    body of ``Snapshot(view_ref)``) has no enclosing slot context and
    counts as READ.

    Descends into Snapshot / Transaction bodies with the brace's scope
    added to ``enclosing``: refs the brace covers are pruned. The
    body is re-entered as a fresh top-level subtree.

    Dynamic (Sort.DYNAMIC) subtrees are opaque: their effect surface is not
    visible at compile time, so we don't descend through them. Any refs
    inside the carrier are hidden from the wrap decision.
    """
    if _is_dynamic(node):
        return
    if isinstance(node, (Snapshot, Transaction)):
        inner = (*enclosing, node.scope)
        for c in node._children:
            yield from _iter_uncovered(c, pass_scope, inner, _top=True)
        return
    if _top and isinstance(node, _VirtualsRef):
        ref_scope = node._root_shape
        if _dominates(pass_scope, ref_scope) and not _covered_by_enclosing(enclosing, ref_scope):
            yield node, False
    mutates = _write_positions(node)
    for slot, child in enumerate(node._children):
        if isinstance(child, _VirtualsRef):
            ref_scope = child._root_shape
            if _dominates(pass_scope, ref_scope) and not _covered_by_enclosing(
                enclosing, ref_scope
            ):
                yield child, slot in mutates
        yield from _iter_uncovered(child, pass_scope, enclosing, _top=False)


def _has_uncovered_ref(node: object, pass_scope: Hashable | None, enclosing: tuple) -> bool:
    return next(_iter_uncovered(node, pass_scope, enclosing), None) is not None


def _has_uncovered_write(node: object, pass_scope: Hashable | None, enclosing: tuple) -> bool:
    return any(is_w for _, is_w in _iter_uncovered(node, pass_scope, enclosing))


def _wrap_kwargs(pass_scope: Hashable | None) -> dict:
    return {"scope": pass_scope} if pass_scope is not None else {}


def _effective_root_is_dyn(child: Nu) -> bool:
    """True if ``child``'s effective root (through Spans) is dynamic.

    The auto-flow pass runs on the raw Term tree, so it cannot reach into the
    compiled ``_effective_sort`` (which needs a Program). We mirror that
    walk here by hand: skip through Span bodies to reach the effective root,
    then check its declared sort.
    """
    node = child
    while isinstance(node, Span) and node._children:
        node = node._children[0]
    return _is_dynamic(node)


def _wrap_flow_child(child: Nu, pass_scope: Hashable | None, enclosing: tuple) -> Nu:
    """Decide how a Flow's direct child gets wrapped."""
    if _effective_root_is_dyn(child):
        # A dynamic subtree's effect surface is opaque at compile time. Leave the
        # branch alone; the runtime dispatcher owns any atomicity concerns.
        return child

    if isinstance(child, Flow):
        # Flow child handles its own children via the recursive walk.
        return child

    if isinstance(child, (Snapshot, Transaction)):
        # External-wrap iff refs escape this brace's coverage. The recursive
        # walk has already added internal wraps for anything the descent
        # found, so anything still uncovered here needs an outer wrap.
        inner = (*enclosing, child.scope)
        if not _has_uncovered_ref(child._children[0], pass_scope, inner):
            return child
        if _has_uncovered_write(child._children[0], pass_scope, inner):
            return Transaction(child, **_wrap_kwargs(pass_scope))
        return Snapshot(child, **_wrap_kwargs(pass_scope))

    if not _has_uncovered_ref(child, pass_scope, enclosing):
        return child
    if _has_uncovered_write(child, pass_scope, enclosing):
        return Transaction(child, **_wrap_kwargs(pass_scope))
    return Snapshot(child, **_wrap_kwargs(pass_scope))


def _walk(node: Nu, pass_scope: Hashable | None, enclosing: tuple) -> Nu:
    if isinstance(node, (Snapshot, Transaction)):
        if _dominates(node.scope, pass_scope):
            # Brace covers everything the pass cares about, skip descent.
            return node
        inner = (*enclosing, node.scope)
        new_children = tuple(_walk(c, pass_scope, inner) for c in node._children)
        if all(n is o for n, o in zip(new_children, node._children, strict=True)):
            return node
        return node._with_children(*new_children)

    if not node._children:
        return node

    new_children = tuple(_walk(c, pass_scope, enclosing) for c in node._children)
    changed = any(n is not o for n, o in zip(new_children, node._children, strict=True))
    new_node = node._with_children(*new_children) if changed else node

    if isinstance(new_node, Flow):
        wrapped = tuple(_wrap_flow_child(c, pass_scope, enclosing) for c in new_node._children)
        if any(w is not c for w, c in zip(wrapped, new_node._children, strict=True)):
            return new_node._with_children(*wrapped)

    return new_node


def auto_flow_atomic(tree: Nu, scope: Hashable | None = None) -> Nu:
    """Rewrites a tree so every branch touching storage sits in the right bracket.

    Walks bottom-up and, at each Flow, replaces each direct child by a
    ``Transaction`` around it if the branch writes storage, a ``Snapshot`` if
    it only reads, and by itself if it does neither. A branch that already
    sits inside a bracket covering it is left alone. What comes back is a new
    tree; the one passed in is untouched.

    A ref counts as a write only where it sits in a slot the enclosing node
    declared as mutating. That is why the pass can tell ``ref.set(v)`` from
    the same ref read as an argument, without knowing anything about either
    node beyond its declaration.

    Args:
        tree: the tree to rewrite.
        scope: the shape whose storage this pass is about, as a tag. None,
            the default, treats every ref as in scope and tags the brackets
            it adds as unscoped. Pass a shape to run one pass per storage in
            a sharded program, each leaving the others' refs alone.

    Notes:
        - A Flow directly under a Flow is left alone. Its own children were
          already bracketed on the way up, and bracketing it again would
          merge branches that were meant to commit separately.
        - A bare subtree that is not a Flow is bracketed too, so
          ``auto_flow_atomic(some_ref)`` resolves on its own without the
          caller wiring a bracket by hand.
        - An existing bracket whose scope covers this pass stops the descent
          entirely. One with a different scope is descended into, and what it
          covers is subtracted from what the pass still has to place.
        - Dynamic subtrees are opaque: their effects are not visible until
          run time, so the pass does not descend through them and does not
          bracket them. Whatever they dispatch to owns its own atomicity.
        - Safe to run over a tree with no storage in it at all: a branch
          with no refs is returned unchanged, and a bracket around a body
          that never reads opens no handle.

    Example:
        app = nu.With(
            nu.kv.rocksdb_navigator(".dbcounter"),
            nu.ui.server(nu.kv.auto_flow_atomic(ui)),
            body=nu.kv.auto_flow_atomic(tick),
        )
    """
    walked = _walk(tree, scope, ())
    return _wrap_flow_child(walked, scope, ())
