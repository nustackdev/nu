"""Nu, rebuilt on the attribute engine.

``symbols`` is Nu as a language defined on ``nu.engine``: the Symbol kinds,
the attributes carrying every Nu concern, and the gates that judge a program.
A description is constructed from the kinds, ``compile``d against the Nu
schema, then queried or gated.

This package is the engine-based successor to ``nu.terms``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.engine import Violation, gate, validate
from nu.engine import compile as _compile
from nu.symbols.attributes import build_schema
from nu.symbols.gates import (
    RULES,
    rule_command_has_write,
    rule_composition,
    rule_flow_has_command,
    rule_query_no_write,
    rule_ref_slots,
    rule_refused,
)
from nu.symbols.kinds import (
    Add,
    Append,
    AsyncFetch,
    BlockingScan,
    Bracket,
    Collect,
    Command,
    Control,
    Copy,
    Delete,
    Eq,
    Filter,
    First,
    Flow,
    ForEachDo,
    Gather,
    IfDo,
    ItemsOf,
    Last,
    Literal,
    Map,
    Mul,
    Not,
    Parallel,
    Policy,
    Query,
    Race,
    Range,
    Reduction,
    Ref,
    Retry,
    ScalarQuery,
    Sequential,
    Snapshot,
    Span,
    Store,
    Strategy,
    StreamQuery,
    Sum,
    Take,
    Transaction,
    TryCatch,
    WhileDo,
)
from nu.symbols.sorts import MATRIX, Effect, Mode, own_label, subsort


if TYPE_CHECKING:
    from nu.engine import Program, Schema
    from nu.engine.symbol import Symbol

__all__ = [
    "MATRIX",
    "RULES",
    "SCHEMA",
    "Add",
    "Append",
    "AsyncFetch",
    "BlockingScan",
    "Bracket",
    "Collect",
    "Command",
    "Control",
    "Copy",
    "Delete",
    "Effect",
    "Eq",
    "Filter",
    "First",
    "Flow",
    "ForEachDo",
    "Gather",
    "IfDo",
    "ItemsOf",
    "Last",
    "Literal",
    "Map",
    "Mode",
    "Mul",
    "Not",
    "Parallel",
    "Policy",
    "Query",
    "Race",
    "Range",
    "Reduction",
    "Ref",
    "Retry",
    "ScalarQuery",
    "Sequential",
    "Snapshot",
    "Span",
    "Store",
    "Strategy",
    "StreamQuery",
    "Sum",
    "Take",
    "Transaction",
    "TryCatch",
    "Violation",
    "WhileDo",
    "compile",
    "gate",
    "own_label",
    "rule_command_has_write",
    "rule_composition",
    "rule_flow_has_command",
    "rule_query_no_write",
    "rule_ref_slots",
    "rule_refused",
    "subsort",
    "validate",
]

# The Nu schema, built and finalized once at import.
SCHEMA: Schema = build_schema()


def compile(description: Symbol) -> Program:
    """Compile a Nu description against the Nu schema."""
    return _compile(description, SCHEMA)
