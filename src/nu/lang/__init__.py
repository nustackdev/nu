"""Nu the language, layer 1 on the engine.

``lang`` is Nu defined on top of ``nu.engine``. Top-level vocabulary:

- ``nu``         - the ``Nu`` base class.
- ``kinds``      - the kind taxonomy (``Ref`` / ``Interaction`` / ``ScalarQuery`` / ...).
- ``args``       - argument type aliases (``IntArg``, ``StrArg``, ...) for kind signatures.
- ``sentinels``  - ``EMPTY`` / ``INVALID`` and their guards.
- ``attributes`` - the attribute concerns (sort, cardinality, effects, execution).
- ``laws``       - ``LAWS`` and the predicate library.
- ``runtime``    - ``Runtime``, ``Context``, ``Budget``, lifecycle helpers.
- ``helpers``    - top-level user-facing entries (``run``, ``eval``, ``astream``, ...).

A Term is built from the kind taxonomy, ``compile``d against the schema,
then ``gate``d or ``validate``d, then driven through an entry.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.engine import (
    Law,
    Predicate,
    Severity,
    Violation,
    gate,
    predicate,
)

from .args import (
    Arg,
    BoolArg,
    BytesArg,
    DictArg,
    FloatArg,
    FrozenSetArg,
    IntArg,
    ListArg,
    NoneArg,
    SetArg,
    StrArg,
    TupleArg,
)
from .attributes import (
    MATRIX,
    Attr,
    Cardinality,
    Effect,
    EffectSet,
    ExecOrder,
    Sort,
    build_schema,
    matrix_sort,
    subsort,
)
from .forms import Form, TypedNu
from .kinds import (
    Action,
    Bracket,
    Command,
    Control,
    Flow,
    Interaction,
    Policy,
    Query,
    Reduction,
    Ref,
    ScalarAction,
    ScalarQuery,
    Span,
    Strategy,
    StreamAction,
    StreamQuery,
)
from .laws import LAWS
from .literal import Literal
from .nu import Nu
from .runtime import Context, Runtime
from .sentinels import (
    EMPTY,
    INVALID,
    UNSET,
    Empty,
    Invalid,
    Sentinel,
    Unset,
    is_empty,
    is_invalid,
    is_sentinel,
)
from .typeinfo import TypeInfo, value_type_for


if TYPE_CHECKING:
    from nu.engine.structure import Schema

__all__ = [
    "EMPTY",
    "INVALID",
    "LAWS",
    "MATRIX",
    "SCHEMA",
    "UNSET",
    "Action",
    "Arg",
    "Attr",
    "BoolArg",
    "Bracket",
    "BytesArg",
    "Cardinality",
    "Command",
    "Context",
    "Control",
    "DictArg",
    "Effect",
    "EffectSet",
    "Empty",
    "ExecOrder",
    "FloatArg",
    "Flow",
    "Form",
    "FrozenSetArg",
    "IntArg",
    "Interaction",
    "Invalid",
    "Law",
    "ListArg",
    "Literal",
    "NoneArg",
    "Nu",
    "Policy",
    "Predicate",
    "Query",
    "Reduction",
    "Ref",
    "Runtime",
    "ScalarAction",
    "ScalarQuery",
    "Sentinel",
    "SetArg",
    "Severity",
    "Sort",
    "Span",
    "StrArg",
    "Strategy",
    "StreamAction",
    "StreamQuery",
    "TupleArg",
    "TypeInfo",
    "TypedNu",
    "Unset",
    "Violation",
    "acollect",
    "aeval",
    "afirst",
    "alast",
    "arun",
    "build_schema",
    "collect",
    "compile",
    "eval",
    "eval_in_loop",
    "first",
    "gate",
    "is_empty",
    "is_invalid",
    "is_sentinel",
    "matrix_sort",
    "predicate",
    "run",
    "run_in_loop",
    "subsort",
    "validate",
    "value_type_for",
]

# The Nu schema, built and finalized once at import.
SCHEMA: Schema = build_schema()

# Re-export the helper entries (compile/validate/run/eval/...) so callers can
# reach them as ``from nu.lang import compile`` too. Loaded after SCHEMA is
# built since helpers.compilation reads SCHEMA at import.
from .helpers import (  # noqa: E402
    acollect,
    aeval,
    afirst,
    alast,
    arun,
    collect,
    compile,
    eval,
    eval_in_loop,
    first,
    run,
    run_in_loop,
    validate,
)
