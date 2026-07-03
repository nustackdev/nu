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
- ``arithmetic`` - numeric ops (AddQuery, SubQuery, MulQuery, PowQuery, AbsQuery, DivModQuery, RoundQuery)
- ``comparison`` - ordering and identity (EqQuery, LtQuery, GtQuery, IsQuery)
- ``logical`` - boolean ops (AndQuery, OrQuery, NotQuery, BoolQuery)
- ``conditional`` - value-yielding branch selection (IfQuery)
- ``bitwise`` - bit ops (BitAndQuery, BitOrQuery, BitXorQuery, LShiftQuery)
- ``cast`` - type construction / conversion (IntQuery, StrQuery, ListQuery, DictQuery, SetQuery)
- ``repr`` - representations (ReprQuery, FormatQuery, BinQuery, HexQuery, OrdQuery, ChrQuery)
- ``access`` - item and attribute access (GetItemQuery, LenQuery, GetAttrQuery, SetAttrCommand)
- ``iteration`` - iterator sources (IterQuery, NextAction, EnumerateQuery, ZipQuery, ReversedQuery)
- ``transform`` - stream-to-stream lenses (MapQuery, FilterQuery, SortedQuery, FlattenQuery)
- ``reduction`` - stream-to-scalar folds (SumQuery, MinQuery, MaxQuery, AnyQuery, AllQuery, CollectQuery)
- ``reflection`` - introspection (TypeQuery, IsInstanceQuery, CallableQuery, IdQuery, HashQuery)
- ``sentinel`` - the EMPTY / INVALID predicates (IsEmptyQuery, IsInvalidQuery)
- ``io`` - console effects through the stdio fabric (PrintCommand, LogCommand, InputAction)
- ``dynamic`` - dynamic evaluation (EvalQuery, ExecQuery, CompileQuery, GlobalsQuery)

Core is the pure Python builtins. The fabric interactions (writing through a
Ref into the Context store, a database, stdio) live in their own fabric dirs -
``nu.context`` owns ``SetCommand`` / ``DeleteCommand`` / ``AttrRef``, not core. The Forms
layer (types, classes) and the Flows / Spans layer (Seq, Par, If, Retry,
Transaction) are later passes with their own homes, not here.
"""

from __future__ import annotations

from nu.core.access import (
    ContainsQuery,
    DelAttrCommand,
    DelItemCommand,
    GetAttrQuery,
    GetItemQuery,
    HasAttrQuery,
    LenQuery,
    SetAttrCommand,
    SetItemCommand,
    SliceQuery,
)
from nu.core.arithmetic import (
    AbsQuery,
    AddQuery,
    DivModQuery,
    DivQuery,
    FloorDivQuery,
    ModQuery,
    MulQuery,
    NegQuery,
    PosQuery,
    PowQuery,
    RoundQuery,
    SubQuery,
)
from nu.core.bitwise import (
    BitAndQuery,
    BitNotQuery,
    BitOrQuery,
    BitXorQuery,
    LShiftQuery,
    RShiftQuery,
)
from nu.core.cast import (
    ByteArrayQuery,
    BytesQuery,
    ComplexQuery,
    DictQuery,
    FloatQuery,
    FrozenSetQuery,
    IntQuery,
    ListQuery,
    SetQuery,
    StrQuery,
    TupleQuery,
)
from nu.core.comparison import EqQuery, GeQuery, GtQuery, IsQuery, LeQuery, LtQuery, NeQuery
from nu.core.conditional import IfQuery, SwitchQuery
from nu.core.dynamic import CompileQuery, EvalQuery, ExecQuery, GlobalsQuery, LocalsQuery
from nu.core.io import InputAction, LogCommand, PrintCommand, input, log, print
from nu.core.iteration import EnumerateQuery, IterQuery, NextAction, ReversedQuery, ZipQuery
from nu.core.literal import LiteralQuery
from nu.core.logical import AndQuery, BoolQuery, NotQuery, OrQuery
from nu.core.reactive import (
    OnChangeQuery,
    OnChildChangeQuery,
    OnChildrenChangeQuery,
    OnDescendantsChangeQuery,
    OnPrimitiveChangeQuery,
)
from nu.core.reduction import (
    AllQuery,
    AnyQuery,
    CollectQuery,
    CountQuery,
    FirstQuery,
    LastQuery,
    MaxQuery,
    MinQuery,
    SumQuery,
)
from nu.core.reflection import (
    CallableQuery,
    DirQuery,
    HashQuery,
    IdQuery,
    IsInstanceQuery,
    IsSubclassQuery,
    TypeQuery,
    VarsQuery,
)
from nu.core.repr import (
    AsciiQuery,
    BinQuery,
    ChrQuery,
    FormatQuery,
    HexQuery,
    OctQuery,
    OrdQuery,
    ReprQuery,
)
from nu.core.sentinel import IsEmptyQuery, IsInvalidQuery, NotEmptyQuery, NotInvalidQuery
from nu.core.transform import (
    FilterQuery,
    FlattenQuery,
    MapQuery,
    SortByQuery,
    SortedQuery,
    UniqueQuery,
)


__all__ = [
    "AbsQuery",
    "AddQuery",
    "AllQuery",
    "AndQuery",
    "AnyQuery",
    "AsciiQuery",
    "BinQuery",
    "BitAndQuery",
    "BitNotQuery",
    "BitOrQuery",
    "BitXorQuery",
    "BoolQuery",
    "ByteArrayQuery",
    "BytesQuery",
    "CallableQuery",
    "ChrQuery",
    "CollectQuery",
    "CompileQuery",
    "ComplexQuery",
    "ContainsQuery",
    "CountQuery",
    "DelAttrCommand",
    "DelItemCommand",
    "DictQuery",
    "DirQuery",
    "DivModQuery",
    "DivQuery",
    "EnumerateQuery",
    "EqQuery",
    "EvalQuery",
    "ExecQuery",
    "FilterQuery",
    "FirstQuery",
    "FlattenQuery",
    "FloatQuery",
    "FloorDivQuery",
    "FormatQuery",
    "FrozenSetQuery",
    "GeQuery",
    "GetAttrQuery",
    "GetItemQuery",
    "GlobalsQuery",
    "GtQuery",
    "HasAttrQuery",
    "HashQuery",
    "HexQuery",
    "IdQuery",
    "IfQuery",
    "InputAction",
    "IntQuery",
    "IsEmptyQuery",
    "IsInstanceQuery",
    "IsInvalidQuery",
    "IsQuery",
    "IsSubclassQuery",
    "IterQuery",
    "LShiftQuery",
    "LastQuery",
    "LeQuery",
    "LenQuery",
    "ListQuery",
    "LiteralQuery",
    "LocalsQuery",
    "LogCommand",
    "LtQuery",
    "MapQuery",
    "MaxQuery",
    "MinQuery",
    "ModQuery",
    "MulQuery",
    "NeQuery",
    "NegQuery",
    "NextAction",
    "NotEmptyQuery",
    "NotInvalidQuery",
    "NotQuery",
    "OctQuery",
    "OnChangeQuery",
    "OnChildChangeQuery",
    "OnChildrenChangeQuery",
    "OnDescendantsChangeQuery",
    "OnPrimitiveChangeQuery",
    "OrQuery",
    "OrdQuery",
    "PosQuery",
    "PowQuery",
    "PrintCommand",
    "RShiftQuery",
    "ReprQuery",
    "ReversedQuery",
    "RoundQuery",
    "SetAttrCommand",
    "SetItemCommand",
    "SetQuery",
    "SliceQuery",
    "SortByQuery",
    "SortedQuery",
    "StrQuery",
    "SubQuery",
    "SumQuery",
    "SwitchQuery",
    "TupleQuery",
    "TypeQuery",
    "UniqueQuery",
    "VarsQuery",
    "ZipQuery",
    "input",
    "log",
    "print",
]
