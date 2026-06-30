"""Nu tree -- traversal, queries, and structural rewrites over Term trees.

The generic metaprogramming toolkit (Layer 2): a top-level package built
on ``lang``, domain-free. Every helper operates on the Term structure
(``.children`` / ``.with_children``) and the ``lang`` kinds (Flow / Ref /
Effect) -- it knows no domain or fabric.

Five modules:

- ``walk``    -- lazy traversals (preorder / postorder / bfs / leaves / ancestors).
- ``query``   -- read-only inspection (find / find_first / count / size / depth).
- ``rewrite`` -- generic Nu -> Nu transforms (map_nodes / replace / wrap / unwrap / ...).
- ``effects`` -- pre-compile effect analysis (is_pure / reads / writes / fabrics / touches_fabric).
- ``flow``    -- flow-aware wrapping primitives (wrap_flows / wrap_flow_children / is_flow).

Layering: ``engine`` holds the primitives (Term, Attribute, compile);
this toolkit sits above ``lang``; domain/fabric-specific rewrite *passes*
(e.g. shape ref annotation in ``domains.shape.rewrite``) sit above this.
"""

from __future__ import annotations

from .effects import (
    fabrics,
    has_write_on_fabric,
    is_pure,
    iter_effects,
    reads,
    touches_fabric,
    writes,
)
from .flow import is_flow, wrap_flow_children, wrap_flows
from .query import count, depth, find, find_first, size
from .rewrite import (
    Transform,
    apply,
    compose,
    conditional_wrap,
    graft,
    map_children,
    map_nodes,
    prune,
    replace,
    unwrap,
    wrap,
)
from .walk import ancestors, bfs, leaves, postorder, preorder


__all__ = [
    "Transform",
    "ancestors",
    "apply",
    "bfs",
    "compose",
    "conditional_wrap",
    "count",
    "depth",
    "fabrics",
    "find",
    "find_first",
    "graft",
    "has_write_on_fabric",
    "is_flow",
    "is_pure",
    "iter_effects",
    "leaves",
    "map_children",
    "map_nodes",
    "postorder",
    "preorder",
    "prune",
    "reads",
    "replace",
    "size",
    "touches_fabric",
    "unwrap",
    "wrap",
    "wrap_flow_children",
    "wrap_flows",
    "writes",
]
