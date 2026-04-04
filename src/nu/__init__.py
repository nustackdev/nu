"""Nu - core library for the Nu ecosystem.

Subpackages:
    terms/       -- algebra terms (Nu, Value, Ref, Op, Span, Sentinel, Arg)
    context/     -- runtime resource container
    ops/         -- all concrete operations
    interfaces/  -- type interfaces + capability mixins
    fn/          -- functional API (typed factories over ops)
    shapes/      -- document data model
    flows/       -- flow operations (control, iteration, parallel, error, timing, io, asserts)
    transform/   -- tree transformations
    graphs/      -- graph data model (stub)
    tables/      -- table data model (stub)
"""

from __future__ import annotations

from . import fn  # noqa: F401
from .context import (
    AnyAttrRef,
    Attributes,
    AttrRef,
    BoolAttrRef,
    BytesAttrRef,
    Context,
    FloatAttrRef,
    IntAttrRef,
    StrAttrRef,
)
from .flows import *  # noqa: F403
from .interfaces import *  # noqa: F403
from .method import AutoInterface, method, prop
from .model import Model
from .ops import *  # noqa: F403
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
from .utils import ensure_nu, typed_value

# combiners must come after star imports to avoid shadowing by interfaces.primitives.none_ module
from .fn.combiners import all_, and_, any_, none_, or_  # noqa: E402


__all__ = [
    "EMPTY",
    "INVALID",
    # Flows — parallel
    "All",
    "Any",
    "AnyAttrRef",
    # Arg types
    "Arg",
    "AutoInterface",
    # Flows — error
    "Assert",
    # Flows — asserts
    "AssertEmpty",
    "AssertEquals",
    "AssertExists",
    "AssertGreaterOrEqual",
    "AssertGreaterThan",
    "AssertLessOrEqual",
    "AssertLessThan",
    "AssertMissing",
    "AssertNotEmpty",
    "AssertNotEquals",
    # Attr refs
    "AttrRef",
    # Context
    "Attributes",
    "BinaryCalc",
    "BinaryCmd",
    "BinaryOp",
    "BoolArg",
    "BoolAttrRef",
    "BytesArg",
    "BytesAttrRef",
    "Calculation",
    "Command",
    "Context",
    # Flows — timing
    "Debounce",
    # Flows — io
    "Debug",
    "Delay",
    "DictArg",
    # Flows — control
    "DoWhile",
    "Empty",
    "FloatArg",
    "FloatAttrRef",
    # Flow & Span
    "Flow",
    # Flows — iteration
    "Fold",
    "ForEach",
    "ForRange",
    "Forever",
    "FrozenSetArg",
    "If",
    "IntArg",
    "IntAttrRef",
    "Invalid",
    "LValue",
    "ListArg",
    "Log",
    # Model
    "Model",
    "NAryCalc",
    "NAryCmd",
    "NAryOp",
    "NoneArg",
    # Nu
    "Nu",
    "Op",
    "Parallel",
    "Print",
    "RValue",
    "Race",
    "Ref",
    "Retry",
    # Sentinel
    "Sentinel",
    "Seq",
    "SetArg",
    "SkipIfEmpty",
    "SkipIfExists",
    "SkipIfMissing",
    "SkipIfNotEmpty",
    "Span",
    "StrArg",
    "StrAttrRef",
    "Switch",
    "TernaryCalc",
    "TernaryCmd",
    "TernaryOp",
    "Throttle",
    "Timed",
    "Timeout",
    # Transform
    "Transform",
    "TryCatch",
    "TupleArg",
    "UnaryCalc",
    "UnaryCmd",
    "UnaryOp",
    "Value",
    "While",
    "all_",
    "ancestors",
    "and_",
    "any_",
    "apply",
    "bfs",
    "compose",
    "count",
    "depth",
    "ensure_nu",
    # Query
    "find",
    "find_first",
    # Display
    "format_tree",
    "graft",
    "is_empty",
    "is_invalid",
    "is_sentinel",
    "leaves",
    "map_children",
    "map_nodes",
    "method",
    "none_",
    "or_",
    "postorder",
    # Walk
    "preorder",
    "print_tree",
    "propagate_special",
    "prop",
    "prune",
    "replace",
    "size",
    "typed_value",
    "unwrap",
    "wrap",
]
