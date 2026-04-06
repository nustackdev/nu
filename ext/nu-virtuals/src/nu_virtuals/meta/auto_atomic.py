"""auto_atomic — Wrap Nu subtrees in Transaction/Snapshot scoped ops."""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu import Nu, find

from ..spans import Snapshot, Transaction


if TYPE_CHECKING:
    from collections.abc import Hashable

    from nu import Nu


__all__ = [
    "auto_atomic",
]


def _has_scope(node: Nu, scope: Hashable) -> bool:
    """Check if a node's subtree contains refs belonging to the given scope."""
    for ref in find(node, lambda n: hasattr(n, "get_root_shape")):
        if ref.get_root_shape() == scope:
            return True
    return False


def _has_pv_write(node: Nu) -> bool:
    """Check if a node's subtree contains impure operations on virtuals refs.

    An impure term is a PV write only if it operates on a virtuals ref
    (PrimitiveRef, ViewRef pre-inline, or FlatRef post-inline).
    Other impure terms (e.g. ed dict stores) are irrelevant to PV atomicity.
    """
    from ..refs.base import PrimitiveRef, ViewRef
    from .flat_ref import FlatRef

    pv_ref_types = (FlatRef, PrimitiveRef, ViewRef)

    for t in find(node, lambda n: isinstance(n, Nu) and not n.is_self_pure):
        if any(isinstance(c, pv_ref_types) for c in find(t, lambda n: isinstance(n, pv_ref_types))):
            return True
    return False


def _conditional_wrap_skip_spans[N: Nu](
    root: N,
    pred: object,
    wrapper: object,
) -> N:
    """Like conditional_wrap but skips existing Transaction/Snapshot ops.

    Explicit Transaction/Snapshot ops placed by user code are respected -
    their contents won't be re-wrapped.
    """
    if pred(root) or root.is_leaf:
        return root

    # Don't recurse into existing Transaction/Snapshot ops
    if isinstance(root, (Transaction, Snapshot)):
        return root

    new_children: list[Nu] = []
    for child in root.children:
        if pred(child):
            new_children.append(wrapper(child))
        else:
            new_children.append(_conditional_wrap_skip_spans(child, pred, wrapper))

    return root.with_children(*new_children)  # type: ignore[arg-type]


def auto_atomic[N: Nu](
    tree: N,
    scope: Hashable | None = None,
) -> N:
    """Wrap each Nu subtree in a ``Transaction`` or ``Snapshot``.

    Walks *tree* bottom-up. Non-Nu children are recursed into so
    their inner Terms get wrapped at their level.

    Purity is resolved at wrap time: impure subtrees get ``Transaction``,
    pure subtrees get ``Snapshot``. No runtime purity check needed.

    Existing Transaction/Snapshot ops (placed explicitly by user code)
    are respected - their contents won't be re-wrapped.

    When ``scope`` is given, only Terms whose refs belong to that scope
    are wrapped. This lets you call auto_atomic multiple times to handle
    different scopes::

        tree = auto_atomic(tree, scope=Services)  # Services Terms only
        tree = auto_atomic(tree)                   # remaining Terms

    When ``scope`` is None, all unwrapped Terms are matched.

    Args:
        tree: Expression tree to rewrite.
        scope: Scope filter. None = wrap all Terms unscoped.

    Returns:
        New tree with Transaction/Snapshot ops injected.
    """
    kwargs: dict = {}
    if scope is not None:
        kwargs["scope"] = scope

    def pred(n: Nu) -> bool:
        if not isinstance(n, Nu):
            return False
        return _has_scope(n, scope) if scope is not None else True

    def wrap(term: Nu) -> Transaction | Snapshot:
        if _has_pv_write(term):
            return Transaction(term, **kwargs)
        return Snapshot(term, **kwargs)

    # If root itself is a matching Nu, wrap it directly
    # (conditional_wrap only wraps children, not the root)
    if pred(tree):
        return wrap(tree)  # type: ignore[return-value]

    return _conditional_wrap_skip_spans(tree, pred, wrap)
