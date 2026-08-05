"""auto_flow_atomic: flow-based bottom-up wrapping for virtuals refs.

Walks the tree bottom-up. At each Flow, wraps every non-Flow direct child
by its tracked effects on virtuals refs whose ``root_shape`` matches
``scope``:

- any WRITE in scope   -> Transaction(child, scope=...)
- only READ in scope   -> Snapshot(child, scope=...)
- no matching effects  -> leave as-is

Flow children of a Flow are left as-is: the bottom-up walk has already
wrapped their own direct children. Existing Snapshot / Transaction
brackets are respected by the ``(scope_pass, scope_brace)`` matrix
documented in ``nu/docs/guides/wrapping.md``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.lang import Flow

from ..interactions.atomicity import Snapshot, Transaction
from ..refs.base import PrimitiveRef, ViewRef


if TYPE_CHECKING:
    from collections.abc import Hashable, Iterator

    from nu.lang import Nu


__all__ = ["auto_flow_atomic"]


_VirtualsRef = (ViewRef, PrimitiveRef)


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
    """
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


def _wrap_flow_child(child: Nu, pass_scope: Hashable | None, enclosing: tuple) -> Nu:
    """Decide how a Flow's direct child gets wrapped."""
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
    """Wrap virtuals-touching Flow branches with Snapshot / Transaction.

    Walks bottom-up. At each Flow, replaces every non-Flow direct child by:

    - ``Transaction(child, scope=scope)`` if the subtree has an uncovered
      WRITE through a virtuals ref matching ``scope``,
    - ``Snapshot(child, scope=scope)`` if it has only READ effects in scope,
    - the child unchanged otherwise.

    Flow children are left alone; the recursive walk has already wrapped
    their own direct children (per-branch, not the whole Flow).

    Existing brackets are respected by the ``(scope_pass, scope_brace)``
    matrix from ``nu/docs/guides/wrapping.md``: a brace that covers ``scope``
    is left alone; a brace with a different scope is descended into and its
    coverage subtracts from the walker's care set.

    ``scope=None`` (default) treats every virtuals ref as in scope; the
    resulting wrapper tag is unscoped.
    """
    return _walk(tree, scope, ())
