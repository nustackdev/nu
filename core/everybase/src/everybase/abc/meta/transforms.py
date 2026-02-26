"""ABC meta-transforms — tree rewrites using abc-specific constructs."""

from __future__ import annotations

from everybase import map_nodes
from everybase.tree import Node


__all__ = [
    "annotate_retries",
]


def annotate_retries[N: Node](tree: N) -> N:
    """Auto-add logging hooks to bare Retry nodes.

    Retry nodes without any hooks get default Log-based hooks:
    - ``on_attempt_fail``: logs warning with error and attempt number
    - ``on_fail``: logs error with final error and attempt count

    Args:
        tree: Tree root.

    Returns:
        New tree with annotated Retry nodes.
    """
    from ..flows.error import Retry
    from ..refs import IntRef, StrRef

    def _annotate(node: Node) -> Node:
        if not isinstance(node, Retry) or node.has_hooks:
            return node

        from ..flows.io import Log

        error = StrRef("error")
        attempt = IntRef("attempt")

        on_attempt_fail = Log(
            "Retry attempt " + attempt.get().to_str() + " failed: " + error.get(),
            level="warning",
        )
        on_fail = Log(
            "Retry exhausted after " + attempt.get().to_str() + " attempts: " + error.get(),
            level="error",
        )

        return Retry(
            node.children[0],
            max_attempts=node.children[1],
            delay=node.children[2],
            backoff=node.children[3],
            on_attempt_fail=on_attempt_fail,
            on_fail=on_fail,
        )

    return map_nodes(tree, _annotate, order="bottom_up")
