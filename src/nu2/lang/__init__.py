"""Nu the language, layer 1 on the engine.

``lang`` is Nu defined on top of ``nu2.engine``. It splits along the same
phase axis the engine uses:

- ``structure``  - the alphabet Nu adds (``Nu`` base, attribute concerns,
  the sort taxonomy classes ``Ref``/``Interaction``/...).
- ``laws``       - the validity rules: ``LAWS`` and the predicate library.
- ``evaluation`` - how programs run: ``NuRuntime``, ``Context``, sentinels.
- ``entry``      - top-level user-facing entries (``run``, ``eval``, ...).

A Term is built from the sort taxonomy, ``compile``d against the schema,
then ``gate``d or ``validate``d, then driven through an entry point.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu2.engine.compilation import compile as _compile
from nu2.engine.validation import (
    Law,
    Predicate,
    Severity,
    Violation,
    gate,
    predicate,
    validate,
)
from nu2.lang.evaluation import (
    EMPTY,
    INVALID,
    Context,
    Empty,
    Invalid,
    NuRuntime,
    Sentinel,
    is_empty,
    is_invalid,
    is_sentinel,
)
from nu2.lang.laws import LAWS
from nu2.lang.structure import (
    MATRIX,
    Attr,
    Bracket,
    Cardinality,
    Command,
    Control,
    Effect,
    EffectSet,
    ExecOrder,
    Flow,
    Interaction,
    Nu,
    Policy,
    Query,
    Reduction,
    Ref,
    ScalarQuery,
    Sort,
    Span,
    Strategy,
    StreamQuery,
    build_schema,
    matrix_sort,
    subsort,
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
    "Attr",
    "Bracket",
    "Cardinality",
    "Command",
    "Context",
    "Control",
    "Effect",
    "EffectSet",
    "Empty",
    "ExecOrder",
    "Flow",
    "Interaction",
    "Invalid",
    "Law",
    "Nu",
    "NuRuntime",
    "Policy",
    "Predicate",
    "Query",
    "Reduction",
    "Ref",
    "ScalarQuery",
    "Sentinel",
    "Severity",
    "Sort",
    "Span",
    "Strategy",
    "StreamQuery",
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
