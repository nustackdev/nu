"""auto_atomic — Wrap Term subtrees in Atomic spans."""

from __future__ import annotations

from typing import TYPE_CHECKING

from everybase import Term
from everybase.meta import conditional_wrap

from ..spans import Atomic


if TYPE_CHECKING:
    from pv.view import View

    from everybase import Node


__all__ = [
    "auto_atomic",
]


def auto_atomic[N: Node](tree: N, shape: type, view_cls: type[View]) -> N:
    """Wrap each Term subtree in its own ``Atomic`` span.

    Walks *tree* bottom-up. Each Term child gets wrapped individually
    in ``Atomic(shape, view_cls, term)``. Non-Term children are
    recursed into so their inner Terms get wrapped at their level.

    Works because Spans are value-transparent — ``Atomic(get())``
    returns the get result.

    Args:
        tree: Expression tree to rewrite.
        shape: Shape class for storage context lookup.
        view_cls: View class to open on top of the storage context.

    Returns:
        New tree with Atomic spans injected.
    """
    return conditional_wrap(
        tree,
        lambda n: isinstance(n, Term),
        lambda term: Atomic(shape, view_cls, term),
    )
