"""Nu layer 0: the domain-free compilation engine.

Symbol and Attribute are the primitives; Schema is the registry; ``compile``
turns a description plus a schema into a Program; ``gate`` and ``validate``
are metaprograms over a compiled program.

The engine knows no sorts, no effects, no execution and holds no global
state. A layer-1 language (Nu) defines kinds and attributes on top of it.
"""

from nu.engine.attribute import Attribute, CycleError, Schema
from nu.engine.meta import Violation, gate, validate
from nu.engine.program import Attr, Program, Rows, compile
from nu.engine.symbol import Symbol, SymbolMeta


__all__ = [
    "Attr",
    "Attribute",
    "CycleError",
    "Program",
    "Rows",
    "Schema",
    "Symbol",
    "SymbolMeta",
    "Violation",
    "compile",
    "gate",
    "validate",
]
