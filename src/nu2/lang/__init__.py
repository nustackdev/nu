"""Nu the language, layer 1 on the engine.

``lang`` is Nu defined on ``nu2.engine``, organized by concern: one module per
attribute group, each carrying that concern's value types, rule functions and
``Attribute`` objects.

- ``sort`` - the structural taxonomy and composition matrix
- ``effects`` - what a program touches in the Context
- ``cardinality`` - how a node yields
- ``execution`` - sync/async, event-loop placement, and exec order
- ``algebra`` - the rewrite-relevant laws a kind obeys
- ``attrs`` - the ``Attr`` name vocabulary shared across concerns
- ``schema`` - assembles every concern into the Nu schema
- ``predicates``, ``laws`` - the validity rules over an attributed program

A description is built from the sort taxonomy, ``attribute``d against the schema,
then queried, ``gate``d or ``validate``d. This package is the attribute-layer
successor to ``nu2.terms``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu2.engine.attribution import (
    Law,
    Predicate,
    Severity,
    Violation,
    gate,
    predicate,
    validate,
)
from nu2.engine.attribution import attribute as _attribute
from nu2.lang.attrs import Attr
from nu2.lang.cardinality import Cardinality
from nu2.lang.effects import Effect, EffectSet
from nu2.lang.execution import ExecOrder
from nu2.lang.laws import LAWS
from nu2.lang.nu import Nu
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
    from nu2.engine.attribution import AttributedTerm
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
    "attribute",
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


def attribute(description: Term) -> AttributedTerm:
    """Attribute a Nu description against the Nu schema."""
    return _attribute(description, SCHEMA)
