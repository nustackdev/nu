"""Layer 4 - declarative access.

This module provides the core Term abstraction for everyshape:
- Term[T] - base for all executable expressions
- Type[T] - unified typed values (literal or computed)
- LValue/RValue - location vs expression duality
- Ref - typed references to locations
- Arg types - standardized input type aliases
"""

from .args import (
    Arg,
    BoolArg,
    BytesArg,
    DictArg,
    FloatArg,
    IntArg,
    ListArg,
    SetArg,
    StrArg,
)
from .combiners import all_, and_, any_, coalesce, ifelse, none_, or_
from .context import Context
from .term import (
    Command,
    Computation,
    LValue,
    Operation,
    PrimitiveRef,
    Ref,
    RValue,
    Term,
    Type,
    ViewRef,
)
from .types import computed, literal


# Backwards compatibility aliases (deprecated)
ValueTerm = Type
TypedValue = Type
LiteralValue = Type
ComputedValue = Type


__all__ = [
    "Arg",
    "BoolArg",
    "BytesArg",
    "Command",
    "Computation",
    "ComputedValue",
    "Context",
    "DictArg",
    "FloatArg",
    "IntArg",
    "LValue",
    "ListArg",
    "Operation",
    "PrimitiveRef",
    "RValue",
    "Ref",
    "SetArg",
    "StrArg",
    "Term",
    "Type",
    "ViewRef",
    "all_",
    "and_",
    "any_",
    "coalesce",
    "computed",
    "ifelse",
    "literal",
    "none_",
    "or_",
]
