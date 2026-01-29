"""everyabc -- Abstract tree construction, traversal, and transformation.

Packages:

    tree/     -- pure tree (Node, Executable, walk, transform, query)
    term/     -- computation (Term, Ref, Morphism, Sentinel)
    flow/     -- ordering (Flow)
    span/     -- cohesion (Span)
    context/  -- runtime (Context, Handle)
"""

from __future__ import annotations

from .context import Context, Handle
from .flow import Flow
from .shape import Shape, Slot
from .span import Span
from .term import (
    EMPTY,
    INVALID,
    Arg,
    BinaryCommand,
    BinaryMorphism,
    BinaryOperation,
    BoolArg,
    BytesArg,
    Command,
    DictArg,
    Empty,
    FloatArg,
    FrozenSetArg,
    IntArg,
    Invalid,
    ListArg,
    LValue,
    Morphism,
    NAryCommand,
    NAryMorphism,
    NAryOperation,
    NoneArg,
    Operation,
    Ref,
    RValue,
    Sentinel,
    SetArg,
    StrArg,
    Term,
    TernaryCommand,
    TernaryMorphism,
    TernaryOperation,
    TupleArg,
    UnaryCommand,
    UnaryMorphism,
    UnaryOperation,
    is_empty,
    is_invalid,
    is_sentinel,
    propagate_special,
)
from .tree import (
    Executable,
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
    "Executable",
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
    "NAryOperation",
    "NAryCommand",
    "UnaryOperation",
    "UnaryCommand",
    "BinaryOperation",
    "BinaryCommand",
    "TernaryOperation",
    "TernaryCommand",
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
    # Arg types
    "Arg",
    "IntArg",
    "FloatArg",
    "StrArg",
    "BoolArg",
    "BytesArg",
    "NoneArg",
    "ListArg",
    "DictArg",
    "SetArg",
    "FrozenSetArg",
    "TupleArg",
    # Shape
    "Shape",
    "Slot",
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
