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
- ``iteration`` - iterator sources (Iter, Next, Enumerate, Zip, Reversed)
- ``transform`` - stream-to-stream lenses (Map, Filter, Sorted, Flatten)
- ``reduction`` - stream-to-scalar folds (Sum, Min, Max, Any, All, Collect)
- ``reflection`` - introspection (Type, IsInstance, Callable, Id, Hash)
- ``sentinel`` - the EMPTY / INVALID predicates (IsEmpty, IsInvalid)
- ``io`` - console / file effects (Print, Input, Open)
- ``dynamic`` - dynamic evaluation (Eval, Exec, Compile, Globals)

Core is the pure Python builtins. The fabric interactions (writing through a
Ref into the Context store, a database, stdio) live in their own fabric dirs -
``nu2.context`` owns ``Set`` / ``Delete`` / ``AttrRef``, not core. The Forms
layer (types, classes) and the Flows / Spans layer (Seq, Par, If, Retry,
Transaction) are later passes with their own homes, not here.
"""

from __future__ import annotations

from nu2.core.access import (
    Contains,
    DelAttr,
    DelItem,
    GetAttr,
    GetItem,
    HasAttr,
    Len,
    SetAttr,
    SetItem,
    Slice,
)
from nu2.core.arithmetic import (
    Abs,
    Add,
    Div,
    DivMod,
    FloorDiv,
    Mod,
    Mul,
    Neg,
    Pos,
    Pow,
    Round,
    Sub,
)
from nu2.core.bitwise import BitAnd, BitNot, BitOr, BitXor, LShift, RShift
from nu2.core.cast import (
    ByteArray,
    Bytes,
    Complex,
    Dict,
    Float,
    FrozenSet,
    Int,
    List,
    Set,
    Str,
    Tuple,
)
from nu2.core.comparison import Eq, Ge, Gt, Is, Le, Lt, Ne
from nu2.core.dynamic import Compile, Eval, Exec, Globals, Locals
from nu2.core.io import Input, Open, Print
from nu2.core.iteration import Enumerate, Iter, Next, Reversed, Zip
from nu2.core.literal import Literal
from nu2.core.logical import And, Bool, Not, Or
from nu2.core.reduction import All, Any, Collect, Count, First, Last, Max, Min, Sum
from nu2.core.reflection import Callable, Dir, Hash, Id, IsInstance, IsSubclass, Type, Vars
from nu2.core.repr import Ascii, Bin, Chr, Format, Hex, Oct, Ord, Repr
from nu2.core.sentinel import IsEmpty, IsInvalid, NotEmpty, NotInvalid
from nu2.core.transform import Filter, Flatten, Map, Sorted, Unique


__all__ = [
    "Abs",
    "Add",
    "All",
    "And",
    "Any",
    "Ascii",
    "Bin",
    "BitAnd",
    "BitNot",
    "BitOr",
    "BitXor",
    "Bool",
    "ByteArray",
    "Bytes",
    "Callable",
    "Chr",
    "Collect",
    "Compile",
    "Complex",
    "Contains",
    "Count",
    "DelAttr",
    "DelItem",
    "Dict",
    "Dir",
    "Div",
    "DivMod",
    "Enumerate",
    "Eq",
    "Eval",
    "Exec",
    "Filter",
    "First",
    "Flatten",
    "Float",
    "FloorDiv",
    "Format",
    "FrozenSet",
    "Ge",
    "GetAttr",
    "GetItem",
    "Globals",
    "Gt",
    "HasAttr",
    "Hash",
    "Hex",
    "Id",
    "Input",
    "Int",
    "Is",
    "IsEmpty",
    "IsInstance",
    "IsInvalid",
    "IsSubclass",
    "Iter",
    "LShift",
    "Last",
    "Le",
    "Len",
    "List",
    "Literal",
    "Locals",
    "Lt",
    "Map",
    "Max",
    "Min",
    "Mod",
    "Mul",
    "Ne",
    "Neg",
    "Next",
    "Not",
    "NotEmpty",
    "NotInvalid",
    "Oct",
    "Open",
    "Or",
    "Ord",
    "Pos",
    "Pow",
    "Print",
    "RShift",
    "Repr",
    "Reversed",
    "Round",
    "Set",
    "SetAttr",
    "SetItem",
    "Slice",
    "Sorted",
    "Str",
    "Sub",
    "Sum",
    "Tuple",
    "Type",
    "Unique",
    "Vars",
    "Zip",
]
