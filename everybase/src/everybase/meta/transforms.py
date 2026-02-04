"""Meta-transforms — tree rewrites for cross-cutting concerns.

These operate on tree *structure*, not individual nodes.
Unlike core transforms (map_nodes, wrap, replace) which act on
single nodes, meta-transforms understand parent/child relationships.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..tree import Node


if TYPE_CHECKING:
    from collections.abc import Callable


__all__ = [
    "conditional_wrap",
]


def conditional_wrap[N: Node](
    root: N,
    pred: Callable[[Node], bool],
    wrapper: Callable[[Node], Node],
) -> N:
    """Wrap each matching child, bottom-up.

    At each node, matching children are wrapped individually via
    ``wrapper(child)``. Non-matching children are recursed into.

    Matching children are **not** recursed into — they are claimed
    whole by the nearest non-matching ancestor, giving the biggest
    matching subtree at each level.

    Args:
        root: Tree root.
        pred: Which children to wrap.
        wrapper: ``child -> wrapped_child``.

    Returns:
        New tree with matching children wrapped.

    Example::

        conditional_wrap(
            tree,
            lambda n: isinstance(n, Term),
            lambda term: Atomic(shape, view_cls, term),
        )
    """
    if pred(root) or root.is_leaf:
        return root

    new_children: list[Node] = []
    for child in root.children:
        if pred(child):
            new_children.append(wrapper(child))
        else:
            new_children.append(conditional_wrap(child, pred, wrapper))

    return root.with_children(*new_children)  # type: ignore[arg-type]
