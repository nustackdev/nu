"""Nu core: the native standard terms.

Concrete atoms layered on ``nu2.lang``'s sort taxonomy - the kinds a real Nu
program is built from. The goal is a 1:1 map of Python's native builtin
functions (the ones that are not methods of a class) onto Nu interactions:
``abs`` -> ``Abs``, ``getattr`` -> ``GetAttr``, ``print`` -> ``Print``. Library
functions (itertools, functools, ...) are not core; they land in ``nu.std`` in a
later pass. Class methods land in extensions later too.

Files group atoms by **Python domain**, not by sort - one file per logical
family, crossing Query / Command / Action as the builtins do:

- ``literal`` - the constant-yielding ScalarQuery
- ``arithmetic`` - numeric ops (Add, Sub, Mul, Pow, Abs, DivMod, Round)
- ``comparison`` - ordering and identity (Eq, Lt, Gt, Is)
- ``logical`` - boolean ops (And, Or, Not, Bool)
- ``bitwise`` - bit ops (BitAnd, BitOr, BitXor, LShift)
- ``cast`` - type construction / conversion (Int, Str, List, Dict, Set)
- ``repr`` - representations (Repr, Format, Bin, Hex, Ord, Chr)
- ``access`` - item and attribute access (GetItem, Len, GetAttr, SetAttr)
- ``iteration`` - iterator sources (Iter, Next, Range, Enumerate, Zip)
- ``transform`` - stream-to-stream lenses (Map, Filter, Sorted, Flatten)
- ``reduction`` - stream-to-scalar folds (Sum, Min, Max, Any, All, Reduce)
- ``reflection`` - introspection (Type, IsInstance, Callable, Id, Hash)
- ``io`` - console / file effects (Print, Input, Open)
- ``dynamic`` - dynamic evaluation (Eval, Exec, Compile, Globals)

Flows and Spans are built in a later pass.

Restructure in progress: the new domain files start as docstring stubs and are
filled by dispatched agents. Until each lands, the names below are re-exported
from ``nu2.core._legacy`` (the old sort-grouped modules) so callers keep
working. As a domain module is implemented, its imports move off ``_legacy``.
"""

from __future__ import annotations

from nu2.core._legacy.arithmetic import Add, Div, Mul, Neg, Sub
from nu2.core._legacy.commands import Delete, Emit, Set
from nu2.core._legacy.flows import If, Par, Seq, While
from nu2.core._legacy.logic import And, Eq, Lt, Not, Or
from nu2.core._legacy.spans import Retry, Scope
from nu2.core._legacy.streams import Take, Watch
from nu2.core.dynamic import Compile, Eval, Exec, Globals, Locals
from nu2.core.iteration import Iter
from nu2.core.literal import Literal
from nu2.core.reduction import Collect, Count, Max, Min, Sum
from nu2.core.transform import Filter, Map


__all__ = [
    "Add",
    "And",
    "Collect",
    "Compile",
    "Count",
    "Delete",
    "Div",
    "Emit",
    "Eq",
    "Eval",
    "Exec",
    "Filter",
    "ForEachDo",
    "Globals",
    "If",
    "Iter",
    "Literal",
    "Locals",
    "Lt",
    "Map",
    "Max",
    "Min",
    "Mul",
    "Neg",
    "Not",
    "Or",
    "Par",
    "Retry",
    "Scope",
    "Seq",
    "Set",
    "Sub",
    "Sum",
    "Take",
    "Transaction",
    "Watch",
    "While",
]
