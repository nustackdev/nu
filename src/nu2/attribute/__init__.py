"""Nu layer 0: the domain-free attribute layer.

Symbol and Attribute are the primitives; Schema is the registry; ``compile``
turns a description plus a schema into a Program; ``gate`` and ``validate``
are metaprograms over a compiled program.

The attribute layer knows no sorts, no effects, no execution and holds no
global state. A layer-1 language (Nu) defines kinds and attributes on top of it.
"""

from nu2.attribute.attribute import Attribute, CycleError, Schema
from nu2.attribute.meta import Law, Predicate, Severity, Violation, gate, predicate, validate
from nu2.attribute.program import Attr, Program, Rows, compile
from nu2.attribute.symbol import Symbol, SymbolMeta


__all__ = [
    "Attr",
    "Attribute",
    "CycleError",
    "Law",
    "Predicate",
    "Program",
    "Rows",
    "Schema",
    "Severity",
    "Symbol",
    "SymbolMeta",
    "Violation",
    "compile",
    "gate",
    "predicate",
    "validate",
]
