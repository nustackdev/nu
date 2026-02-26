"""ABC meta-transforms — tree rewrites using abc-specific constructs."""

from __future__ import annotations

from everybase import map_nodes
from everybase.tree import Node


__all__ = [
    "annotate_retries",
    "annotate_steps",
]


def annotate_retries[N: Node](tree: N) -> N:
    """Add logging hooks to all Retry nodes.

    Wraps every Retry with Log-based hooks for ``on_attempt_fail`` and
    ``on_fail``.  If the Retry already has hooks, they are preserved —
    a ``Seq(Log(...), existing_hook)`` wraps the original.

    Args:
        tree: Tree root.

    Returns:
        New tree with annotated Retry nodes.
    """
    from ..flows.control import Seq
    from ..flows.error import Retry
    from ..flows.io import Log
    from ..refs import IntRef, StrRef

    def _annotate(node: Node) -> Node:
        if not isinstance(node, Retry):
            return node

        error = StrRef("error")
        attempt = IntRef("attempt")

        log_af = Log(
            "retry attempt " + attempt.get().to_str() + " failed: " + error.get(),
            level="warning",
        )
        log_fail = Log(
            "retry exhausted after " + attempt.get().to_str() + " attempts: " + error.get(),
            level="error",
        )

        existing_af = node.on_attempt_fail
        existing_fail = node.on_fail

        on_af = Seq(log_af, existing_af) if existing_af else log_af
        on_fail = Seq(log_fail, existing_fail) if existing_fail else log_fail

        return node.with_children(
            *node.children[:4],
            on_af,
            node.children[5],  # on_success — unchanged
            on_fail,
        )

    return map_nodes(tree, _annotate, order="bottom_up")


def annotate_steps[N: Node](tree: N) -> N:
    """Add step logging to Seq nodes.

    Each child of a Seq gets a ``Log`` before and after it, showing
    which step is running and when it completes.

    Args:
        tree: Tree root.

    Returns:
        New tree with step-annotated Seq nodes.
    """
    from ..flows.control import Seq
    from ..flows.io import Log

    def _annotate(node: Node) -> Node:
        if not isinstance(node, Seq) or len(node.children) < 2:
            return node

        total = len(node.children)
        new_children: list = []
        for i, child in enumerate(node.children, 1):
            label = repr(child)
            new_children.append(Log(f"[{i}/{total}] {label}"))
            new_children.append(child)
            new_children.append(Log(f"[{i}/{total}] done"))

        return node.with_children(*new_children)

    return map_nodes(tree, _annotate, order="bottom_up")
