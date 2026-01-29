"""Tree layer -- nodes, traversal, transforms, queries, and Exec base.

Structural operations only. No domain semantics.
"""

from __future__ import annotations

from .exec import Executable
from .node import Node
from .query import count, depth, find, find_first, size
from .transform import (
    Transform,
    apply,
    compose,
    graft,
    map_children,
    map_nodes,
    prune,
    replace,
    unwrap,
    wrap,
)
from .walk import ancestors, bfs, leaves, postorder, preorder


__all__ = [  # noqa: RUF022
    # Node
    "Node",
    "Executable",
    # Walk
    "preorder",
    "postorder",
    "bfs",
    "leaves",
    "ancestors",
    # Transform
    "Transform",
    "compose",
    "apply",
    "map_children",
    "map_nodes",
    "replace",
    "wrap",
    "unwrap",
    "graft",
    "prune",
    # Query
    "find",
    "find_first",
    "count",
    "size",
    "depth",
]
