"""Nu the language, layer 1 on the engine.

``lang`` is Nu defined on top of ``nu2.engine``. Top-level vocabulary:

- ``nu``         - the ``Nu`` base class.
- ``kinds``      - the kind taxonomy (``Ref`` / ``Interaction`` / ``ScalarQuery`` / ...).
- ``args``       - argument type aliases (``IntArg``, ``StrArg``, ...) for kind signatures.
- ``sentinels``  - ``EMPTY`` / ``INVALID`` and their guards.
- ``attributes`` - the attribute concerns (sort, cardinality, effects, execution, algebra).
- ``laws``       - ``LAWS`` and the predicate library.
- ``runtime``    - ``Runtime``, ``Context``, ``Budget``, lifecycle helpers.
- ``helpers``    - top-level user-facing entries (``run``, ``eval``, ``astream``, ...).

A Term is built from the kind taxonomy, ``compile``d against the schema,
then ``gate``d or ``validate``d, then driven through an entry.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu2.engine import (
    Law,
    Predicate,
    Severity,
    Violation,
    gate,
    predicate,
    validate,
)
from nu2.engine import compile as _compile

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
from .kinds import (
    Bracket,
    Command,
    Control,
    Flow,
    Interaction,
    Policy,
    Query,
    Reduction,
    Ref,
    ScalarQuery,
    Span,
    Strategy,
    StreamQuery,
)
from .laws import LAWS
from .nu import Nu
from .runtime import Context, Runtime
from .sentinels import (
    EMPTY,
    INVALID,
    Empty,
    Invalid,
    Sentinel,
    is_empty,
    is_invalid,
    is_sentinel,
)


if TYPE_CHECKING:
    from nu2.engine.compilation import Program
    from nu2.engine.structure import Schema, Term

__all__ = [
    "EMPTY",
    "INVALID",
    "LAWS",
    "MATRIX",
    "SCHEMA",
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
    "FrozenSetArg",
    "IntArg",
    "Interaction",
    "Invalid",
    "Law",
    "ListArg",
    "NoneArg",
    "Nu",
    "Policy",
    "Predicate",
    "Query",
    "Reduction",
    "Ref",
    "Runtime",
    "ScalarQuery",
    "Sentinel",
    "SetArg",
    "Severity",
    "Sort",
    "Span",
    "StrArg",
    "Strategy",
    "StreamQuery",
    "TupleArg",
    "Violation",
    "build_schema",
    "compile",
    "gate",
    "is_empty",
    "is_invalid",
    "is_sentinel",
    "matrix_sort",
    "predicate",
    "subsort",
    "validate",
]

# The Nu schema, built and finalized once at import.
SCHEMA: Schema = build_schema()


def compile(term: Term) -> Program:
    """Compile a Nu Term against the Nu schema; return a runnable Program."""
    return _compile(term, SCHEMA)
