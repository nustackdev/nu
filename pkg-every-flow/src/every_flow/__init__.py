"""every_flow -- Synchronous flow primitives for everyabc.

Six base flows + Var + Const for building executable topologies.
All flows are synchronous and use Context.

Flows:
    Seq       -- sequential children
    If        -- conditional: condition, then/else branches
    While     -- loop while condition is truthy
    ForRange  -- counted loop with optional index Var
    Parallel  -- concurrent children via ThreadPoolExecutor
    TryCatch  -- try/catch/finally with optional error Var

Communication:
    Var[T]    -- mutable in-memory variable extending Ref[T]

Utilities:
    Const[T]  -- literal value wrapped as a Term
"""

from __future__ import annotations

from ._util import Const
from .cond import If
from .error import TryCatch
from .io import Print
from .loops import ForRange, While
from .parallel import Parallel
from .seq import Seq
from .var import Var


__all__ = [
    "Const",
    "ForRange",
    "If",
    "Parallel",
    "Print",
    "Seq",
    "TryCatch",
    "Var",
    "While",
]
