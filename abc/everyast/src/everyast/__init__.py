"""everyast -- Abstract tree construction, traversal, and transformation.

Two layers:

    ast/   -- pure tree data structure (Node, walk, transform, query)
    defs/  -- topology node contracts (Exec, Term, Flow, Span) and core types

The ast layer is structure without semantics.
The defs layer adds topological meaning as abstract contracts.
"""

from __future__ import annotations

from .ast import (
    Node,
    Transform,
    ancestors,
    apply,
    bfs,
    compose,
    count,
    depth,
    find,
    find_first,
    graft,
    leaves,
    map_children,
    map_nodes,
    postorder,
    preorder,
    prune,
    replace,
    size,
    unwrap,
    wrap,
)
from .defs import (
    EMPTY,
    INVALID,
    Empty,
    Exec,
    Flow,
    Invalid,
    Sentinel,
    Span,
    Term,
    is_empty,
    is_invalid,
    is_sentinel,
    propagate_special,
)


__all__ = [  # noqa: RUF022
    # Node
    "Node",
    # Topology nodes
    "Exec",
    "Term",
    "Flow",
    "Span",
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
    # Sentinel
    "Sentinel",
    "Empty",
    "Invalid",
    "EMPTY",
    "INVALID",
    "is_empty",
    "is_invalid",
    "is_sentinel",
    "propagate_special",
]
