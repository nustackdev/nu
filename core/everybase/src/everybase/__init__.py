"""everybase — Core library for the every ecosystem.

Subpackages:
    tree/  -- immutable tree nodes
    core/  -- computation layer (term/flow/span/context/exec)
    meta/  -- tree meta-tools (walk, query, transform, rewrites)
    abc/   -- base implementations: types, values, morphisms, capabilities
"""

from __future__ import annotations

from .core import (
    EMPTY,
    INVALID,
    Arg,
    BinaryCommand,
    BinaryMorphism,
    BinaryOperation,
    BoolArg,
    BytesArg,
    Command,
    Context,
    DictArg,
    Empty,
    Executable,
    FloatArg,
    Flow,
    FrozenSetArg,
    IntArg,
    Invalid,
    ListArg,
    LValue,
    Model,
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
from .meta import (
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
from .tree import Node


# Primitive refs — lazy to avoid circular import
# (abc.refs → abc → abc.flows → everybase.Flow)
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
        from .abc import refs as _refs

        return getattr(_refs, _PRIM_REF_NAMES[name])
    if name == "annotate_retries":
        from .abc.meta import annotate_retries

        return annotate_retries
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)


__all__ = [  # noqa: RUF022
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
    # Meta-transforms
    "annotate_retries",
]
