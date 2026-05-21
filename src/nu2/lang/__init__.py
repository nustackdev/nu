"""Nu the language, layer 1 on the attribute layer.

``lang`` is Nu defined on ``nu2.attribute``, organized by concern: one module
per attribute group, each carrying that concern's value types, rule functions
and ``Attribute`` objects.

- ``sort`` - the structural taxonomy and composition matrix
- ``effects`` - what a program touches in the Context
- ``cardinality`` - how a node yields
- ``execution`` - sync/async, event-loop placement, and exec order
- ``algebra`` - the rewrite-relevant laws a kind obeys
- ``attrs`` - the ``Attr`` name vocabulary shared across concerns
- ``schema`` - assembles every concern into the Nu schema
- ``predicates``, ``laws`` - the validity rules over a compiled program

A description is built from the sort taxonomy, ``compile``d against the schema,
then queried, ``gate``d or ``validate``d. This package is the attribute-layer
successor to ``nu2.terms``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu2.attribute import Law, Predicate, Severity, Violation, gate, predicate, validate
from nu2.attribute import compile as _compile
from nu2.lang.attrs import Attr
from nu2.lang.cardinality import Cardinality
from nu2.lang.effects import Effect, EffectSet
from nu2.lang.execution import ExecOrder
from nu2.lang.laws import LAWS
from nu2.lang.schema import build_schema
from nu2.lang.sentinels import (
    EMPTY,
    INVALID,
    Empty,
    Invalid,
    Sentinel,
    is_empty,
    is_invalid,
    is_sentinel,
)
from nu2.lang.sort import (
    MATRIX,
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
    Sort,
    Span,
    Strategy,
    StreamQuery,
    matrix_sort,
    subsort,
)


if TYPE_CHECKING:
    from nu2.attribute import Program, Schema
    from nu2.attribute.symbol import Symbol

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
    "Control",
    "Effect",
    "EffectSet",
    "Empty",
    "ExecOrder",
    "Flow",
    "Interaction",
    "Invalid",
    "Law",
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


def compile(description: Symbol) -> Program:
    """Compile a Nu description against the Nu schema."""
    return _compile(description, SCHEMA)
