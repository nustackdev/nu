"""Nu terms - the four Nu kinds + shared types + authoring utilities.

Layout (see projects/nu/model/programming/components.md + interactions.md):

    Nu                  - primitive (nu.py)
    ├── Ref             - addressable location (ref.py)
    ├── Interaction     - compute or mutate (interaction.py)
    │   ├── Query       - functional construction (query.py)
    │   │   └── Literal, Stream, ScalarQuery / Unary / Binary / Ternary
    │   └── Command     - imperative mutation (command.py)
    │       └── Flow, ScalarCommand / Unary / Binary / Ternary
    ├── Form            - typed descriptor (interface.py; rename later)
    └── ContextManager  - bracket hooks (context_manager.py)

Shared: types.py (Mode, sup, Sentinel, EMPTY/INVALID, Direction, TrackedEffect,
Arg types, T_co). Analysis + Form/Interface descriptors: utils.py.
"""

from .command import (
    BinaryCommand,
    Command,
    Flow,
    ScalarCommand,
    TernaryCommand,
    UnaryCommand,
)
from .context_manager import ContextManager
from .interaction import Interaction
from .interface import Interface, TypedNu
from .nu import LValue, Nu, NuIndepComm, RValue
from .query import (
    BinaryQuery,
    Literal,
    Query,
    ScalarQuery,
    Stream,
    TernaryQuery,
    UnaryQuery,
)
from .ref import Ref
from .types import (
    EMPTY,
    INVALID,
    Arg,
    BoolArg,
    BytesArg,
    DictArg,
    Direction,
    Empty,
    FloatArg,
    FrozenSetArg,
    IntArg,
    Invalid,
    ListArg,
    Mode,
    NoneArg,
    Sentinel,
    SetArg,
    StrArg,
    T_co,
    TrackedEffect,
    TupleArg,
    is_empty,
    is_invalid,
    is_sentinel,
    propagate_special,
    sup,
)
from .utils import is_pure, tracked_effects
# Re-exports from invocation/ for back-compat of legacy stdlib + ext callsites.
from ..invocation import FuncCall, FuncCallCmd, Invocation, Invoke, MethodCall, MethodCallCmd


__all__ = [
    "EMPTY",
    "INVALID",
    "Arg",
    "BinaryCommand",
    "BinaryQuery",
    "BoolArg",
    "BytesArg",
    "Command",
    "ContextManager",
    "DictArg",
    "Direction",
    "Empty",
    "FloatArg",
    "Flow",
    "FrozenSetArg",
    "FuncCall",
    "FuncCallCmd",
    "IntArg",
    "Interaction",
    "Interface",
    "Invalid",
    "Invocation",
    "Invoke",
    "LValue",
    "ListArg",
    "Literal",
    "MethodCall",
    "MethodCallCmd",
    "Mode",
    "NoneArg",
    "Nu",
    "NuIndepComm",
    "Query",
    "RValue",
    "Ref",
    "ScalarCommand",
    "ScalarQuery",
    "Sentinel",
    "SetArg",
    "StrArg",
    "Stream",
    "T_co",
    "TernaryCommand",
    "TernaryQuery",
    "TrackedEffect",
    "TupleArg",
    "TypedNu",
    "UnaryCommand",
    "UnaryQuery",
    "is_empty",
    "is_invalid",
    "is_pure",
    "is_sentinel",
    "propagate_special",
    "sup",
    "tracked_effects",
]
