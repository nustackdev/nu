"""auto_atomic — Wrap Term subtrees in Atomic spans."""

from __future__ import annotations

from typing import TYPE_CHECKING

from everybase import Term
from everybase.meta import conditional_wrap

from ..spans import Atomic


if TYPE_CHECKING:
    from collections.abc import Hashable

    from pv.view import View

    from everybase import Node


__all__ = [
    "auto_atomic",
]


def auto_atomic[N: Node](
    tree: N,
    scope: Hashable | None = None,
    view_cls: type[View] | None = None,
) -> N:
    """Wrap each Term subtree in its own ``Atomic`` span.

    Walks *tree* bottom-up. Each Term child gets wrapped individually
    in ``Atomic(term, scope=..., view_cls=...)``. Non-Term children are
    recursed into so their inner Terms get wrapped at their level.

    Args:
        tree: Expression tree to rewrite.
        scope: Scope for storage context lookup. None = unscoped (default).
        view_cls: View class to open. If None, uses Atomic default (DictView).

    Returns:
        New tree with Atomic spans injected.
    """
    kwargs: dict = {}
    if scope is not None:
        kwargs["scope"] = scope
    if view_cls is not None:
        kwargs["view_cls"] = view_cls

    return conditional_wrap(
        tree,
        lambda n: isinstance(n, Term),
        lambda term: Atomic(term, **kwargs),
    )
