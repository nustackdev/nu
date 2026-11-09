"""What the bracket passes read off a tree: which refs no bracket covers yet.

Both passes, ``auto_flow_atomic`` and ``atomic``, walk a term the same way: a
Ref names the store it reads, a node declares the slots it mutates, an
enclosing bracket covers the refs of its scope, and a dynamic subtree is
opaque. This module is that shared walk.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import nu
from nu.lang import Effect

from ..interactions.atomicity import Snapshot, Transaction
from ..refs.base import PrimitiveRef, ViewRef


if TYPE_CHECKING:
    from collections.abc import Hashable, Iterator

    from nu.lang import Nu


__all__ = [
    "dominates",
    "iter_uncovered",
]


_VirtualsRef = (ViewRef, PrimitiveRef)


def dominates(broader: Hashable | None, specific: Hashable | None) -> bool:
    """True iff ``broader`` covers everything ``specific`` refers to.

    ``broader`` is a brace scope or the pass scope; ``specific`` is a
    ref's root shape or the pass scope.

    A universal scope (``None``) dominates any specific scope; a concrete
    scope dominates only itself.
    """
    return broader is None or broader is specific


def _covered_by_enclosing(enclosing: tuple, ref_scope: Hashable) -> bool:
    return any(dominates(s, ref_scope) for s in enclosing)


def iter_uncovered(
    node: Nu,
    pass_scope: Hashable | None,
    enclosing: tuple,
    _top: bool = True,
) -> Iterator[tuple[object, bool]]:
    """Yield ``(ref, is_write)`` for uncovered virtuals refs in a subtree.

    Only refs the pass cares about, that no enclosing brace covers.

    Refs are classified as ``nu.tree.node_effects`` binds them: WRITE in a
    mutation slot of an enclosing op, READ elsewhere, and not at all in a
    structural slot (address structure, never evaluated). A top-level Ref (a subtree that IS a Ref, e.g. the
    body of ``Snapshot(view_ref)``) has no enclosing slot context and
    counts as READ.

    Descends into Snapshot / Transaction bodies with the brace's scope
    added to ``enclosing``: refs the brace covers are pruned. The
    body is re-entered as a fresh top-level subtree.

    Dynamic (Sort.DYNAMIC) subtrees are opaque: their effect surface is not
    visible at compile time, so we don't descend through them. Any refs
    inside the carrier are hidden from the wrap decision.
    """
    if nu.tree.is_dynamic(node):
        return
    if isinstance(node, (Snapshot, Transaction)):
        inner = (*enclosing, node.scope)
        for c in nu.tree.children(node):
            yield from iter_uncovered(c, pass_scope, inner, _top=True)
        return
    if _top and isinstance(node, _VirtualsRef):
        ref_scope = node._root_shape
        if dominates(pass_scope, ref_scope) and not _covered_by_enclosing(enclosing, ref_scope):
            yield node, False
    for ref, effect in nu.tree.node_effects(node):
        if isinstance(ref, _VirtualsRef):
            ref_scope = ref._root_shape
            if dominates(pass_scope, ref_scope) and not _covered_by_enclosing(enclosing, ref_scope):
                yield ref, effect is Effect.WRITE
    for child in nu.tree.children(node):
        yield from iter_uncovered(child, pass_scope, enclosing, _top=False)
