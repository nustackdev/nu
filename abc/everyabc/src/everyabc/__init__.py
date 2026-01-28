"""everyabc -- Abstract tree construction, traversal, and transformation.

Packages:

    tree/     -- pure tree (Node, Exec, walk, transform, query)
    term/     -- computation (Term, Ref, Morphism, Sentinel)
    flow/     -- ordering (Flow)
    span/     -- cohesion (Span)
    context/  -- runtime (Context, Handle)
"""

from __future__ import annotations

from .context import Context, Handle
from .flow import Flow
from .span import Span
from .term import (
    EMPTY,
    INVALID,
    BinaryMorphism,
    Command,
    Empty,
    Fetchable,
    Invalid,
    LValue,
    Morphism,
    NAryMorphism,
    Operation,
    Ref,
    RValue,
    Sentinel,
    Shape,
    ShapeMeta,
    Slot,
    SlotDescriptor,
    Term,
    TernaryMorphism,
    UnaryMorphism,
    is_empty,
    is_invalid,
    is_sentinel,
    propagate_special,
)
from .tree import (
    Exec,
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


__all__ = [  # noqa: RUF022
    # Tree
    "Node",
    "Exec",
    # Term
    "Term",
    "LValue",
    "RValue",
    "Ref",
    "Morphism",
    "NAryMorphism",
    "UnaryMorphism",
    "BinaryMorphism",
    "TernaryMorphism",
    "Operation",
    "Command",
    "Fetchable",
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
    # Shape
    "Shape",
    "ShapeMeta",
    "Slot",
    "SlotDescriptor",
    # Flow & Span
    "Flow",
    "Span",
    # Context
    "Context",
    "Handle",
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
