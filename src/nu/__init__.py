"""Nu — core library for the Nu ecosystem.

Subpackages:
    terms/       -- algebra terms (Value, Ref, Op, Span, Sentinel, Arg)
    context/     -- runtime resource container
    ops/         -- all concrete operations
    interfaces/  -- type interfaces + capability mixins
    shapes/      -- document data model
    transform/   -- tree transformations
    graphs/      -- graph data model (stub)
    tables/      -- table data model (stub)
"""

from __future__ import annotations

from .context import Attributes, Context
from .model import Model
from .ops.flows import Flow
from .terms import (
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
    Executable,
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
    Node,
    NoneArg,
    Operation,
    Ref,
    RValue,
    Sentinel,
    SetArg,
    Span,
    StrArg,
    Term,
    TernaryCommand,
    TernaryMorphism,
    TernaryOperation,
    TupleArg,
    UnaryCommand,
    UnaryMorphism,
    UnaryOperation,
    Value,
    is_empty,
    is_invalid,
    is_sentinel,
    propagate_special,
)
from .transform import (
    Transform,
    ancestors,
    apply,
    bfs,
    compose,
    count,
    depth,
    find,
    find_first,
    format_tree,
    graft,
    leaves,
    map_children,
    map_nodes,
    postorder,
    preorder,
    print_tree,
    prune,
    replace,
    size,
    unwrap,
    wrap,
)


# Primitive refs — lazy to avoid circular import
_PRIM_REF_NAMES = {
    "PrimRef": "PrimRef",
    "PrimIntRef": "IntRef",
    "PrimFloatRef": "FloatRef",
    "PrimStrRef": "StrRef",
    "PrimBoolRef": "BoolRef",
    "PrimBytesRef": "BytesRef",
    "PrimAnyRef": "AnyRef",
}


def __getattr__(name: str) -> object:
    if name in _PRIM_REF_NAMES:
        from .context import attr_refs as _refs

        return getattr(_refs, _PRIM_REF_NAMES[name])
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)


__all__ = [
    # Tree
    "Node",
    "Executable",
    # Term
    "Term",
    "LValue",
    "RValue",
    "Value",
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
    # Model
    "Model",
    # Flow & Span
    "Flow",
    "Span",
    # Context
    "Attributes",
    "Context",
    # Primitive refs
    "PrimRef",
    "PrimIntRef",
    "PrimFloatRef",
    "PrimStrRef",
    "PrimBoolRef",
    "PrimBytesRef",
    "PrimAnyRef",
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
]
