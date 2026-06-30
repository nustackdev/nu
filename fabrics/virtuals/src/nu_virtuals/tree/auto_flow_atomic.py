"""auto_flow_atomic — per-branch Atomic wrapping driven by effect analysis.

Walk the tree, threading an ambient list of enclosing Bracket scopes. At
each Flow, replace every direct child by inspecting which of its effects
remain *uncovered* given (pass scope, ambient).

For a virtuals ref ``r``::

    covers(⊥, r)       = True
    covers(T, r)       = root_shape(r) is T
    cares(⊥, r)        = True                  (any virtuals ref)
    cares(S, r)        = root_shape(r) is S
    uncovered(pass, ambient, r)
                       = cares(pass, r)
                         ∧ ∀ b ∈ ambient: ¬covers(b, r)

Decisions:

- **descend** into a Bracket iff some ``r`` could satisfy ``uncovered``
  under ``ambient + {bracket.scope}``. Equivalently: the combined
  ambient does not fully cover the pass's care set.
- **external-wrap** a Bracket-as-Flow-child iff its tracked effects
  contain at least one ref uncovered under that same combined ambient.

Both wraps use ``scope_pass`` for the new Bracket. Composed nestings
like ``Tx(⊥, Tx(T, …))`` or ``Tx(S, Tx(T, …))`` are intentional.

See guides/wrapping.md for the full matrix.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.terms import Effect, Flow, tracked_effects
from nu.terms.span import Bracket

from ..refs.base import PrimitiveRef, ViewRef
from ..refs.flat import FlatRef
from ..spans.atomic import Snapshot, Transaction


if TYPE_CHECKING:
    from collections.abc import Hashable

    from nu.terms import Nu


__all__ = [
    "auto_flow_atomic",
]


_VIRTUALS_REFS = (ViewRef, PrimitiveRef, FlatRef)


def _fully_covered(scope_pass: Hashable | None, ambient: tuple) -> bool:
    """The pass's care set is already covered by ambient — no descent needed."""
    for cov in ambient:
        if cov is None:
            return True
        if scope_pass is not None and cov is scope_pass:
            return True
    return False


def _is_uncovered(
    ref: object,
    scope_pass: Hashable | None,
    ambient: tuple,
) -> bool:
    if not isinstance(ref, _VIRTUALS_REFS):
        return False
    shape = ref.get_root_shape()
    if scope_pass is not None and shape is not scope_pass:
        return False
    for cov in ambient:
        if cov is None or cov is shape:
            return False
    return True


def _uncovered_effects(
    node: Nu,
    scope_pass: Hashable | None,
    ambient: tuple,
) -> tuple[bool, bool]:
    """Return (has_write, has_read) over uncovered virtuals refs."""
    has_write = False
    has_read = False
    for ref, eff in tracked_effects(node):
        if not _is_uncovered(ref, scope_pass, ambient):
            continue
        if eff is Effect.WRITE:
            has_write = True
        else:
            has_read = True
    return has_write, has_read


def _pick_wrap(
    node: Nu,
    has_write: bool,
    has_read: bool,
    scope_pass: Hashable | None,
) -> Nu:
    if has_write:
        return Transaction(node, scope=scope_pass)
    if has_read:
        return Snapshot(node, scope=scope_pass)
    return node


def _wrap_flow_child(
    child: Nu,
    scope_pass: Hashable | None,
    ambient: tuple,
) -> Nu:
    if isinstance(child, Flow):
        return child  # inner Flow already processed by recursion
    if isinstance(child, Bracket):
        combined = (*ambient, getattr(child, "scope", None))
        has_write, has_read = _uncovered_effects(child, scope_pass, combined)
        return _pick_wrap(child, has_write, has_read, scope_pass)
    has_write, has_read = _uncovered_effects(child, scope_pass, ambient)
    return _pick_wrap(child, has_write, has_read, scope_pass)


def auto_flow_atomic(tree: Nu, *, scope: Hashable | None = None) -> Nu:
    """Wrap each Flow's branches in Atomic boundaries driven by effects.

    See module docstring for full semantics.
    """

    def _walk(node: Nu, ambient: tuple) -> Nu:
        if isinstance(node, Bracket):
            combined = (*ambient, getattr(node, "scope", None))
            if _fully_covered(scope, combined):
                return node
            ambient = combined
        if not node._children:
            return node
        new_children = tuple(_walk(c, ambient) for c in node._children)
        if all(n is o for n, o in zip(new_children, node._children, strict=True)):
            new_node = node
        else:
            new_node = node._with_children(new_children)
        if isinstance(new_node, Flow):
            wrapped = tuple(_wrap_flow_child(c, scope, ambient) for c in new_node._children)
            if any(w is not c for w, c in zip(wrapped, new_node._children, strict=True)):
                return new_node._with_children(wrapped)
        return new_node

    return _walk(tree, ())
