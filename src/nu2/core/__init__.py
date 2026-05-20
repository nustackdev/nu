"""Nu core: the native standard symbols.

Concrete atoms layered on ``nu2.lang``'s sort taxonomy - the kinds a real Nu
program is built from. Each module is one family:

- ``arithmetic`` - literals and the numeric ScalarQueries
- ``logic`` - comparison and boolean ScalarQueries
- ``streams`` - StreamQuery sources and stream-to-stream operators
- ``reductions`` - Reductions that fold a stream to one value
- ``commands`` - Commands that write the Context
- ``flows`` - Strategies and Controls that compose Commands
- ``spans`` - Brackets and Policies that govern a body

This is an intermediate set for validating the language; expect it to move
or be reshaped once the law work lands.
"""

from __future__ import annotations

from nu2.core.arithmetic import Add, Div, Literal, Mul, Neg, Sub
from nu2.core.commands import Delete, Emit, Set
from nu2.core.flows import If, Par, Seq, While
from nu2.core.logic import And, Eq, Lt, Not, Or
from nu2.core.reductions import Count, Max, Min, Sum
from nu2.core.spans import Retry, Scope
from nu2.core.streams import Filter, Map, Range, Take, Watch


__all__ = [
    "Add",
    "And",
    "Count",
    "Delete",
    "Div",
    "Emit",
    "Eq",
    "Filter",
    "If",
    "Literal",
    "Lt",
    "Map",
    "Max",
    "Min",
    "Mul",
    "Neg",
    "Not",
    "Or",
    "Par",
    "Range",
    "Retry",
    "Scope",
    "Seq",
    "Set",
    "Sub",
    "Sum",
    "Take",
    "Watch",
    "While",
]
