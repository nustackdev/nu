"""auto_distribute - wrap concurrent op children in Teleport.

Finds parallel-capable nodes (Parallel, Race, ParAny) and wraps their
children in Teleport for distributed execution. Children already
wrapped in Teleport are skipped.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.interactions.flow.strategy import ParAny
from nu.terms.flow import Parallel, Race
from nu.tree.rewrite import map_nodes

from ..spans.teleport import Teleport


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.terms import Nu

type Strategy = Callable[[int, int], object]
"""Worker selection: (child_index, child_count) -> worker_tag."""


__all__ = [
    "auto_distribute",
    "round_robin",
]

_CONCURRENT_OPS = (Parallel, Race, ParAny)


def round_robin(index: int, count: int) -> int:
    """Assign workers by index (0, 1, 2, ...)."""
    return index


def auto_distribute(
    tree: Nu,
    strategy: Strategy = round_robin,
) -> Nu:
    """Wrap concurrent op children in Teleport.

    Children already wrapped in Teleport are left as-is.
    """

    def _rewrite(node: Nu) -> Nu:
        if not isinstance(node, _CONCURRENT_OPS):
            return node
        if not node._children:
            return node

        new_children: list = []
        changed = False
        for i, child in enumerate(node._children):
            if isinstance(child, Teleport):
                new_children.append(child)
            else:
                tag = strategy(i, len(node._children))
                new_children.append(Teleport(child, worker=tag))
                changed = True

        if not changed:
            return node
        return node._with_children(tuple(new_children))

    return map_nodes(tree, _rewrite, order="bottom_up")
