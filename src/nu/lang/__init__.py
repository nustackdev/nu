"""Nu the language, layer 1 on the attribute layer.

``lang`` is Nu defined on ``nu.attribute``, organized by concern: one module
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
successor to ``nu.terms``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.attribute import Law, Predicate, Severity, Violation, gate, predicate, validate
from nu.attribute import compile as _compile
from nu.lang.attrs import Attr
from nu.lang.cardinality import Cardinality
from nu.lang.effects import Effect, EffectSet
from nu.lang.execution import ExecOrder
from nu.lang.laws import LAWS
from nu.lang.schema import build_schema
from nu.lang.sort import (
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
    from nu.attribute import Program, Schema
    from nu.attribute.symbol import Symbol

__all__ = [
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
    "ExecOrder",
    "Flow",
    "Interaction",
    "Law",
    "Policy",
    "Predicate",
    "Query",
    "Reduction",
    "Ref",
    "ScalarQuery",
    "Severity",
    "Sort",
    "Span",
    "Strategy",
    "StreamQuery",
    "Violation",
    "compile",
    "gate",
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
