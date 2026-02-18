"""everybase.meta — Tree meta-tools.

Walk, query, transform, and structural rewrites.
"""

from .display import format_tree, print_tree
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
from .transforms import conditional_wrap
from .walk import ancestors, bfs, leaves, postorder, preorder


__all__ = [  # noqa: RUF022
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
    # Display
    "format_tree",
    "print_tree",
    # Meta-transforms
    "conditional_wrap",
]
