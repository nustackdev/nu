"""Meta-transforms — tree rewrites for cross-cutting concerns.

These operate on tree *structure*, not individual nodes.
Unlike core transforms (map_nodes, wrap, replace) which act on
single nodes, meta-transforms group and restructure siblings.
"""

from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from collections.abc import Callable

    from ..core.tree import Node


__all__ = [
    "conditional_wrap",
]


def conditional_wrap(
    root: Node,
    pred: Callable[[Node], bool],
    wrapper: Callable[[tuple[Node, ...]], Node],
) -> Node:
    """Group contiguous children matching *pred* and wrap each group.

    Bottom-up: recurses into non-matching children first, then at each
    non-leaf node groups contiguous runs of children that satisfy *pred*
    and replaces each run with ``wrapper(run)``.

    Matching children are **not** recursed into — they are claimed by
    the nearest non-matching ancestor.

    Args:
        root: Tree root.
        pred: Which children to group.
        wrapper: ``(matched_children,) -> replacement_node``.

    Returns:
        New tree with matched runs wrapped.

    Example::

        # Wrap contiguous Term children in Atomic spans
        conditional_wrap(
            tree,
            lambda n: isinstance(n, Term),
            lambda terms: Atomic(shape, view_cls, *terms),
        )
    """
    if pred(root):
        return root

    if root.is_leaf:
        return root

    # Recurse into non-matching children first (bottom-up).
    processed: list[Node] = []
    for child in root.children:
        if pred(child):
            processed.append(child)
        else:
            processed.append(conditional_wrap(child, pred, wrapper))

    # Group contiguous matching children into runs, wrap each.
    new_children: list[Node] = []
    run: list[Node] = []
    for child in processed:
        if pred(child):
            run.append(child)
        else:
            if run:
                new_children.append(wrapper(tuple(run)))
                run = []
            new_children.append(child)
    if run:
        new_children.append(wrapper(tuple(run)))

    return root.with_children(*new_children)
