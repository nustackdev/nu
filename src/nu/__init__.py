"""Nu - core library for the Nu ecosystem.

Subpackages:
    terms/       -- algebra terms (Nu, Value, Ref, Op, Span, Sentinel, Arg)
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
from .interfaces.capabilities import *  # noqa: F403
from .interfaces.collections_abc import *  # noqa: F403
from .interfaces.types import *  # noqa: F403
from .interfaces.values import *  # noqa: F403
from .method import AutoInterface, method, prop
from .model import Model
from .ops import fn
from .utils import ensure_nu, typed_value
from .ops import *  # noqa: F403
from .ops.combiners import all_, and_, any_, none_, or_
from .ops.flows import *  # noqa: F403
from .terms import (
    EMPTY,
    INVALID,
    Arg,
    BinaryCalc,
    BinaryCmd,
    BinaryOp,
    BoolArg,
    BytesArg,
    Calculation,
    Command,
    DictArg,
    Empty,
    FloatArg,
    FrozenSetArg,
    IntArg,
    Invalid,
    ListArg,
    LValue,
    NAryCalc,
    NAryCmd,
    NAryOp,
    NoneArg,
    Nu,
    Op,
    Ref,
    RValue,
    Sentinel,
    SetArg,
    Span,
    StrArg,
    TernaryCalc,
    TernaryCmd,
    TernaryOp,
    TupleArg,
    UnaryCalc,
    UnaryCmd,
    UnaryOp,
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


# Primitive refs - lazy to avoid circular import
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
    # Nu
    "Nu",
    "LValue",
    "RValue",
    "Value",
    "Ref",
    "Op",
    "NAryOp",
    "UnaryOp",
    "BinaryOp",
    "TernaryOp",
    "Calculation",
    "Command",
    "NAryCalc",
    "NAryCmd",
    "UnaryCalc",
    "UnaryCmd",
    "BinaryCalc",
    "BinaryCmd",
    "TernaryCalc",
    "TernaryCmd",
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
