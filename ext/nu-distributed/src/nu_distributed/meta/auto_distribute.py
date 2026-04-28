"""auto_distribute - wrap concurrent op children in Teleport.

Finds parallel-capable nodes (NuIndepComm via `|`, plus ParAll/Race/ParAny) and
wraps their children in Teleport for distributed execution.

Children already wrapped in Teleport are skipped.
Follows the same deformation pattern as auto_atomic in nu-virtuals.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.interactions.command.flow.parallel import ParAll, ParAny, Race
from nu.terms._compat_nu import NuIndepComm
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

_CONCURRENT_OPS = (NuIndepComm, ParAll, Race, ParAny)


def round_robin(index: int, count: int) -> int:
    """Assign workers by index (0, 1, 2, ...)."""
    return index


def auto_distribute(
    tree: Nu,
    strategy: Strategy = round_robin,
) -> Nu:
    """Wrap concurrent op children in Teleport.

    Finds parallel-capable nodes (NuIndepComm via `|`, plus ParAll, Race, ParAny)
    and wraps each child in Teleport with a worker tag assigned by strategy.

    Children already wrapped in Teleport are left as-is.

    Args:
        tree: Tree to rewrite.
        strategy: Worker assignment function (index, count) -> tag.

    Returns:
        New tree with Teleport injected around concurrent children.
    """

    def _rewrite(node: Nu) -> Nu:
        if not isinstance(node, _CONCURRENT_OPS):
            return node
        if not node.children:
            return node

        new_children: list = []
        changed = False
        for i, child in enumerate(node.children):
            if isinstance(child, Teleport):
                new_children.append(child)
            else:
                tag = strategy(i, len(node.children))
                new_children.append(Teleport(child, worker=tag))
                changed = True

        if not changed:
            return node
        return node._with_children(*new_children)

    return map_nodes(tree, _rewrite, order="bottom_up")
