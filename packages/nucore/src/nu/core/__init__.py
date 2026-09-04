"""Nu core: the native standard terms.

Concrete atoms layered on ``nu.lang``'s sort taxonomy - the kinds a real Nu
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
- ``logical`` - boolean ops (And, Or, Not, ToBool)
- ``conditional`` - value-yielding branch selection (If)
- ``bitwise`` - bit ops (BitAnd, BitOr, BitXor, LShift)
- ``cast`` - type construction / conversion (ToInt, ToStr, ToList, ToDict, ToSet)
- ``repr`` - representations (Repr, Format, Bin, Hex, Ord, Chr)
- ``access`` - item and attribute access (GetItem, Len, GetAttr, SetAttr)
- ``iteration`` - iterator sources (Iter, Next, Enumerate, Zip, Reversed)
- ``transform`` - stream-to-stream lenses (Map, Filter, Sorted, Flatten)
- ``reduction`` - stream-to-scalar folds (Sum, Min, Max, AnyOf, AllOf, Collect)
- ``reflection`` - introspection (Type, IsInstance, Callable, Id, Hash)
- ``sentinel`` - the EMPTY / INVALID predicates (IsEmpty, IsInvalid)
- ``io`` - console effects through the stdio fabric (Print, Input).
        Logging lives at ``nu.std.logging`` -- a Python ``logging`` module wrap.
- ``dynamic`` - host-namespace escape hatches (Globals, Locals)

Core is the pure Python builtins. The fabric interactions (writing through a
Ref into the Context store, a database, stdio) live in their own fabric dirs -
``nu.context`` owns ``SetCmd`` / ``Delete`` / ``AttrRef``, not core. The Forms
layer (types, classes) and the Flows / Spans layer (Seq, Par, If, Retry,
Transaction) are later passes with their own homes, not here.
"""

from __future__ import annotations

from nu.core.access import (
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
from nu.core.arithmetic import (
    Abs,
    Add,
    Div,
    DivMod,
    FloorDiv,
    MatMul,
    Mod,
    Mul,
    Neg,
    Pos,
    Pow,
    Round,
    Sub,
)
from nu.core.bitwise import (
    BitAnd,
    BitNot,
    BitOr,
    BitXor,
    LShift,
    RShift,
)
from nu.core.cast import (
    ToByteArray,
    ToBytes,
    ToComplex,
    ToDict,
    ToFloat,
    ToFrozenSet,
    ToInt,
    ToList,
    ToSet,
    ToStr,
    ToTuple,
)
from nu.core.cast_fns import (
    dict,
    float,
    frozenset,
    int,
    list,
    set,
    str,
    tuple,
)
from nu.core.comparison import Eq, Ge, Gt, Is, Le, Lt, Ne
from nu.core.conditional import If, Switch
from nu.core.dynamic import Globals, Locals
from nu.core.io import Input, Print, input, print
from nu.core.iteration import Enumerate, Iter, Next, Reversed, Zip
from nu.core.literal import Literal
from nu.core.logical import And, Not, Or, ToBool, bool
from nu.core.reduction import (
    AllOf,
    AnyOf,
    Collect,
    Count,
    First,
    Last,
    Max,
    Min,
    Sum,
)
from nu.core.reflection import (
    Callable,
    Dir,
    Hash,
    Id,
    IsInstance,
    IsSubclass,
    Type,
    Vars,
)
from nu.core.repr import (
    Ascii,
    Bin,
    Chr,
    Format,
    Hex,
    Oct,
    Ord,
    Repr,
)
from nu.core.sentinel import IsEmpty, IsInvalid, NotEmpty, NotInvalid
from nu.core.transform import (
    Filter,
    Flatten,
    Map,
    SortBy,
    Sorted,
    Unique,
)
from nu.reactive.interactions import (
    OnChange,
    OnChildChange,
    OnChildrenChange,
    OnDescendantsChange,
    OnPrimitiveChange,
)


__all__ = [
    "Abs",
    "Add",
    "AllOf",
    "And",
    "AnyOf",
    "Ascii",
    "Bin",
    "BitAnd",
    "BitNot",
    "BitOr",
    "BitXor",
    "Callable",
    "Chr",
    "Collect",
    "Contains",
    "Count",
    "DelAttr",
    "DelItem",
    "Dir",
    "Div",
    "DivMod",
    "Enumerate",
    "Eq",
    "Filter",
    "First",
    "Flatten",
    "FloorDiv",
    "Format",
    "Ge",
    "GetAttr",
    "GetItem",
    "Globals",
    "Gt",
    "HasAttr",
    "Hash",
    "Hex",
    "Id",
    "If",
    "Input",
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
    "Literal",
    "Locals",
    "Lt",
    "Map",
    "MatMul",
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
    "OnChange",
    "OnChildChange",
    "OnChildrenChange",
    "OnDescendantsChange",
    "OnPrimitiveChange",
    "Or",
    "Ord",
    "Pos",
    "Pow",
    "Print",
    "RShift",
    "Repr",
    "Reversed",
    "Round",
    "SetAttr",
    "SetItem",
    "Slice",
    "SortBy",
    "Sorted",
    "Sub",
    "Sum",
    "Switch",
    "ToBool",
    "ToByteArray",
    "ToBytes",
    "ToComplex",
    "ToDict",
    "ToFloat",
    "ToFrozenSet",
    "ToInt",
    "ToList",
    "ToSet",
    "ToStr",
    "ToTuple",
    "Type",
    "Unique",
    "Vars",
    "Zip",
    "bool",
    "dict",
    "float",
    "frozenset",
    "input",
    "int",
    "list",
    "print",
    "set",
    "str",
    "tuple",
]
