"""Structure: the alphabet Nu adds on top of ``engine.structure``.

Four layers:

- ``nu``    - the ``Nu`` base class, the user-facing brand on every construct.
- ``args``  - ``Arg[T]`` / ``IntArg`` / ``StrArg`` ... aliases for kind slots.
- ``attrs`` - one module per attribute concern (sort, cardinality, effects,
  execution, algebra) plus the ``Attr`` name vocabulary and ``build_schema``.
- ``sorts`` - the user-facing Term classes (``Ref``, ``Interaction``,
  ``Query``, ``ScalarQuery``, ``Command``, ``Flow``, ``Span``, ...) that
  declare the sort and cardinality bindings on their classes.
"""

from __future__ import annotations

from nu2.lang.structure.args import (
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
from nu2.lang.structure.attrs import (
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
from nu2.lang.structure.nu import Nu
from nu2.lang.structure.sorts import (
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


__all__ = [
    "MATRIX",
    "Arg",
    "Attr",
    "BoolArg",
    "Bracket",
    "BytesArg",
    "Cardinality",
    "Command",
    "Control",
    "DictArg",
    "Effect",
    "EffectSet",
    "ExecOrder",
    "FloatArg",
    "Flow",
    "FrozenSetArg",
    "IntArg",
    "Interaction",
    "ListArg",
    "NoneArg",
    "Nu",
    "Policy",
    "Query",
    "Reduction",
    "Ref",
    "ScalarQuery",
    "SetArg",
    "Sort",
    "Span",
    "StrArg",
    "Strategy",
    "StreamQuery",
    "TupleArg",
    "build_schema",
    "matrix_sort",
    "subsort",
]
