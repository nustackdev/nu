"""Nu terms - the four Nu kinds + shared types + authoring utilities.

Layout (see projects/nu/model/programming/components.md + interactions.md):

    Nu                  - primitive (nu.py)
    ├── Ref             - addressable location (ref.py)
    ├── Interaction     - compute or mutate (interaction.py)
    │   ├── Query       - functional construction (query.py)
    │   │   └── Literal, NAryScalar / Unary / Binary / Ternary, Stream
    │   └── Command     - imperative mutation (command.py)
    │       └── Atomic, Flow
    ├── Form            - typed descriptor (interface.py; rename later)
    └── ContextManager  - bracket hooks (context_manager.py)

Shared: types.py (Mode, sup, Sentinel, EMPTY/INVALID, Direction, TrackedEffect,
Arg types, T_co). Analysis + Form/Interface descriptors: utils.py.
"""

from .command import Atomic, Command, Flow
from .context_manager import ContextManager
from .injection import FuncCall, FuncCallCmd, MethodCall, MethodCallCmd
from .interaction import Interaction
from .interface import Interface, TypedNu
from .nu import LValue, Nu, NuIndepComm, RValue
from .query import (
    BinaryScalar,
    Literal,
    NAryScalar,
    Query,
    Stream,
    TernaryScalar,
    UnaryScalar,
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
from .utils import AutoInterface, is_pure, method, prop, tracked_effects


__all__ = [
    "EMPTY",
    "INVALID",
    "Arg",
    "Atomic",
    "AutoInterface",
    "BinaryScalar",
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
    "LValue",
    "ListArg",
    "Literal",
    "MethodCall",
    "MethodCallCmd",
    "Mode",
    "NAryScalar",
    "NoneArg",
    "Nu",
    "NuIndepComm",
    "Query",
    "RValue",
    "Ref",
    "Sentinel",
    "SetArg",
    "StrArg",
    "Stream",
    "T_co",
    "TernaryScalar",
    "TrackedEffect",
    "TupleArg",
    "TypedNu",
    "UnaryScalar",
    "is_empty",
    "is_invalid",
    "is_pure",
    "is_sentinel",
    "method",
    "prop",
    "propagate_special",
    "sup",
    "tracked_effects",
]
