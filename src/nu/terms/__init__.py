"""Nu terms - the public surface during the task-083 phased rewrite.

Two layers re-exported here:

- **Compat** (from `_compat_*` modules): the pre-refactor surface.
  Downstream (`interactions/`, `tree/`, `ext/...`) still imports these
  names. ARCH-NOTE: full mechanical migration to the new core is
  deferred; the compat shim retains legacy semantics so the runtime
  keeps working while downstream gets swept incrementally.
- **New** (from `protocol`, `nu`, `ref`, `query`, `command`, `flow`,
  `span`, `effects`, `sentinels`, `types`): the new shape this refactor
  builds. Not wired into the runtime yet (Phase D does that).

Where the names overlap (`Nu`, `Ref`, `Query`, `Command`, `Flow`,
`ScalarQuery`, `ScalarCommand`, `Literal`, `Sentinel`, `EMPTY`,
`INVALID`), the compat class wins at the unqualified import site so
downstream keeps running. The new shapes are reachable under explicit
module paths (`nu.terms.protocol.Nu`, `nu.terms.nu.NuBase`,
`nu.terms.ref.Ref`, etc.).

New-only names (`NuBase`, `Effect`, `Realization`, `ExecState`, `Span`,
`Bracket`, `Policy`, `Snapshot`, `Transaction`, `Retry`, `TryCatch`,
`Sequential`, `Parallel`, `Race`, `Gather`, `IfDo`, `ForEachDo`,
`WhileDo`, `Strategy`, `Control`, `Reduction`, `StreamQuery`) are
re-exported here too.
"""

# Re-exports from invocation/ for back-compat of legacy stdlib + ext callsites.
from ..invocation import FuncCall, FuncCallCmd, Invocation, Invoke, MethodCall, MethodCallCmd
from ._compat_command import (
    BinaryCommand,
    Command,
    Flow,
    ScalarCommand,
    TernaryCommand,
    UnaryCommand,
)
from ._compat_context_manager import ContextManager
from ._compat_interaction import Interaction
from ._compat_interface import Interface, TypedNu
from ._compat_nu import LValue, Nu, NuIndepComm, RValue
from ._compat_query import (
    BinaryQuery,
    Literal,
    Query,
    ScalarQuery,
    Stream,
    TernaryQuery,
    UnaryQuery,
)
from ._compat_ref import Ref
from ._compat_types import (
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
from ._compat_utils import is_pure, tracked_effects
from .flow import (
    Control,
    ForEachDo,
    Gather,
    IfDo,
    Parallel,
    Race,
    Sequential,
    Strategy,
    WhileDo,
)

# New-layer names that don't clash with legacy.
from .nu import NuBase, walk
from .query import Reduction, StreamQuery
from .span import Bracket, Policy, Retry, Snapshot, Span, Transaction, TryCatch
from .types import Effect, ExecState, Realization


__all__ = [
    "EMPTY",
    "INVALID",
    "Arg",
    "BinaryCommand",
    "BinaryQuery",
    "BoolArg",
    "Bracket",
    "BytesArg",
    "Command",
    "ContextManager",
    "Control",
    "DictArg",
    "Direction",
    "Effect",
    "Empty",
    "ExecState",
    "FloatArg",
    "Flow",
    "ForEachDo",
    "FrozenSetArg",
    "FuncCall",
    "FuncCallCmd",
    "Gather",
    "IfDo",
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
    "NuBase",
    "NuIndepComm",
    "Parallel",
    "Policy",
    "Query",
    "RValue",
    "Race",
    "Realization",
    "Reduction",
    "Ref",
    "Retry",
    "ScalarCommand",
    "ScalarQuery",
    "Sentinel",
    "Sequential",
    "SetArg",
    "Snapshot",
    "Span",
    "StrArg",
    "Strategy",
    "Stream",
    "StreamQuery",
    "T_co",
    "TernaryCommand",
    "TernaryQuery",
    "TrackedEffect",
    "Transaction",
    "TryCatch",
    "TupleArg",
    "TypedNu",
    "UnaryCommand",
    "UnaryQuery",
    "WhileDo",
    "is_empty",
    "is_invalid",
    "is_pure",
    "is_sentinel",
    "propagate_special",
    "sup",
    "tracked_effects",
    "walk",
]
