"""auto_atomic — Wrap Term subtrees in Atomic spans."""

from __future__ import annotations

from typing import TYPE_CHECKING

from everybase import Term, find
from everybase.meta import conditional_wrap

from ..spans import Atomic


if TYPE_CHECKING:
    from collections.abc import Hashable

    from pv.view import View

    from everybase import Node


__all__ = [
    "auto_atomic",
]


def _has_scope(node: Node, scope: Hashable) -> bool:
    """Check if a node's subtree contains refs belonging to the given scope."""
    for ref in find(node, lambda n: hasattr(n, "get_root_shape")):
        if ref.get_root_shape() == scope:
            return True
    return False


def auto_atomic[N: Node](
    tree: N,
    scope: Hashable | None = None,
    view_cls: type[View] | None = None,
) -> N:
    """Wrap each Term subtree in its own ``Atomic`` span.

    Walks *tree* bottom-up. Non-Term children are recursed into so
    their inner Terms get wrapped at their level.

    When ``scope`` is given, only Terms whose refs belong to that scope
    are wrapped. This lets you call auto_atomic multiple times to handle
    different scopes::

        tree = auto_atomic(tree, scope=Services)  # Services Terms only
        tree = auto_atomic(tree)                   # remaining Terms

    When ``scope`` is None, all unwrapped Terms are matched.

    Args:
        tree: Expression tree to rewrite.
        scope: Scope filter and Atomic scope. None = wrap all Terms unscoped.
        view_cls: View class to open. If None, uses Atomic default (DictView).

    Returns:
        New tree with Atomic spans injected.
    """
    kwargs: dict = {}
    if scope is not None:
        kwargs["scope"] = scope
    if view_cls is not None:
        kwargs["view_cls"] = view_cls

    def pred(n: Node) -> bool:
        if not isinstance(n, Term):
            return False
        return _has_scope(n, scope) if scope is not None else True

    return conditional_wrap(tree, pred, lambda term: Atomic(term, **kwargs))
