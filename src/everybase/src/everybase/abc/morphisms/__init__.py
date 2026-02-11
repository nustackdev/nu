"""Concrete morphisms for everybase.

Structure:

op_  — Python operators (syntactic)
  op_arithmetic.py: NegOp, AbsOp, PosOp, AddOp, SubOp, MulOp, DivOp, etc.
  op_comparison.py: EqOp, NeOp, GtOp, LtOp, GeOp, LeOp, IdCompOp
  op_logical.py: NotOp, BoolOp, AndOp, OrOp
  op_bitwise.py: BitwiseNotOp, BitwiseAndOp, BitwiseOrOp, XorOp, LShiftOp, RShiftOp

fn_  — Builtin functions & higher-order
  fn_transform.py: MapOp, FilterOp, ReduceOp, SortedOp, ReversedOp
  fn_search.py: FindOp, FindIndexOp
  fn_aggregate.py: SumOp, MinOp, MaxOp, AnyOp, AllOp
  fn_conversion.py: ToIntOp, ToStrOp, ToBoolOp, ToFloatOp, ToBytesOp, etc.
  fn_call.py: FuncCall/Op/Cmd, MethodCall/Op/Cmd

gen_ — General patterns (protocol-level)
  gen_access.py: AtOp, SliceOp, LenOp, ContainsOp
  gen_attr.py: GetAttrOp, SetAttrOp, DelAttrOp
  gen_special.py: IsEmptyOp, IsNaNOp, NotEmptyOp, NotNaNOp
  gen_conditional.py: ConditionalOp

type_ — Concrete type methods
  type_str.py: String-specific ops (UpperOp, SplitOp, JoinOp, etc.)
  type_bytes.py: Bytes-specific ops (DecodeOp, HexOp, etc.)

abc_ — ABC-level operations (pure) + commands (impure)
  abc_sequence.py: FirstOp, LastOp, IndexOfOp, CountOp, AppendCmd, InsertCmd, PopCmd
  abc_mapping.py: KeysOp, ValuesOp, ItemsOp, GetOp, SetItemCmd, DeleteItemCmd, UpdateCmd
  abc_set.py: UnionOp, IntersectionOp, DifferenceOp, etc., AddCmd, RemoveCmd, DiscardCmd
  cmd_collection.py: ClearCmd (shared across collection types)

All morphisms use every.Morphism base classes and implement apply().
"""

# ── abc_ — ABC-level operations + commands ────────────────────────────────────
from .abc_mapping import (
    DeleteItemCmd,
    GetOp,
    ItemsOp,
    KeysOp,
    SetItemCmd,
    UpdateCmd,
    ValuesOp,
)
from .abc_sequence import (
    AppendCmd,
    CountOp,
    ExtendCmd,
    FirstOp,
    IndexOfOp,
    InsertCmd,
    LastOp,
    PopCmd,
    RemoveValueCmd,
)
from .abc_set import (
    AddCmd,
    DifferenceOp,
    DiscardCmd,
    IntersectionOp,
    IsDisjointOp,
    IsSubsetOp,
    IsSupersetOp,
    RemoveCmd,
    SymmetricDifferenceOp,
    UnionOp,
)
from .cmd_collection import ClearCmd

# ── fn_ — Builtin functions & higher-order ──────────────────────────────────
from .fn_aggregate import (
    AllOp,
    AnyOp,
    MaxOp,
    MinOp,
    SumOp,
)
from .fn_call import (
    FuncCall,
    FuncCallCmd,
    FuncCallOp,
    MethodCall,
    MethodCallCmd,
    MethodCallOp,
)
from .fn_conversion import (
    ToBoolOp,
    ToBytesOp,
    ToFloatOp,
    ToIntOp,
    ToListOp,
    ToSetOp,
    ToStrOp,
    ToTupleOp,
)
from .fn_search import (
    FindIndexOp,
    FindOp,
)
from .fn_transform import (
    FilterOp,
    MapOp,
    ReduceOp,
    ReversedOp,
    SortedOp,
)

# ── gen_ — General patterns ─────────────────────────────────────────────────
from .gen_access import (
    AtOp,
    ContainsOp,
    LenOp,
    SliceOp,
)
from .gen_attr import DelAttrOp, GetAttrOp, SetAttrOp
from .gen_conditional import ConditionalOp
from .gen_special import IsEmptyOp, IsNaNOp, NotEmptyOp, NotNaNOp

# ── op_ — Python operators ──────────────────────────────────────────────────
from .op_arithmetic import (
    AbsOp,
    AddOp,
    DivOp,
    FloorDivOp,
    ModOp,
    MulOp,
    NegOp,
    PosOp,
    PowOp,
    SubOp,
)
from .op_bitwise import (
    BitwiseAndOp,
    BitwiseNotOp,
    BitwiseOrOp,
    LShiftOp,
    RShiftOp,
    XorOp,
)
from .op_comparison import EqOp, GeOp, GtOp, IdCompOp, LeOp, LtOp, NeOp
from .op_logical import AndOp, BoolOp, NotOp, OrOp

# ── type_ — Concrete type methods ───────────────────────────────────────────
from .type_bytes import (
    BytesCountOp,
    BytesEndsWithOp,
    BytesFindOp,
    BytesLowerOp,
    BytesLStripOp,
    BytesReplaceOp,
    BytesRStripOp,
    BytesSplitOp,
    BytesStartsWithOp,
    BytesStripOp,
    BytesUpperOp,
    DecodeOp,
    HexOp,
)
from .type_str import (
    CapitalizeOp,
    CenterOp,
    CountSubstringOp,
    EncodeOp,
    EndsWithOp,
    IsAlnumOp,
    IsAlphaOp,
    IsDigitOp,
    IsSpaceOp,
    JoinOp,
    LJustOp,
    LowerOp,
    LStripOp,
    ReplaceOp,
    RJustOp,
    RSplitOp,
    RStripOp,
    SplitOp,
    StartsWithOp,
    SwapCaseOp,
    TitleOp,
    UpperOp,
    ZFillOp,
)
from .type_str import (
    FindOp as StrFindOp,
)
from .type_str import (
    RFindOp as StrRFindOp,
)
from .type_str import (
    StripOp as StrStripOp,
)


__all__ = [  # noqa: RUF022
    # op_ — Python operators
    "AbsOp",
    "AddOp",
    "DivOp",
    "FloorDivOp",
    "ModOp",
    "MulOp",
    "NegOp",
    "PosOp",
    "PowOp",
    "SubOp",
    "EqOp",
    "GeOp",
    "GtOp",
    "IdCompOp",
    "LeOp",
    "LtOp",
    "NeOp",
    "AndOp",
    "BoolOp",
    "NotOp",
    "OrOp",
    "BitwiseAndOp",
    "BitwiseNotOp",
    "BitwiseOrOp",
    "LShiftOp",
    "RShiftOp",
    "XorOp",
    # fn_ — Builtin functions & higher-order
    "AllOp",
    "AnyOp",
    "MaxOp",
    "MinOp",
    "SumOp",
    "FuncCall",
    "FuncCallCmd",
    "FuncCallOp",
    "MethodCall",
    "MethodCallCmd",
    "MethodCallOp",
    "ToBoolOp",
    "ToBytesOp",
    "ToFloatOp",
    "ToIntOp",
    "ToListOp",
    "ToSetOp",
    "ToStrOp",
    "ToTupleOp",
    "CountOp",
    "FindIndexOp",
    "FindOp",
    "FirstOp",
    "IndexOfOp",
    "JoinOp",
    "LastOp",
    "FilterOp",
    "MapOp",
    "ReduceOp",
    "ReversedOp",
    "SortedOp",
    # gen_ — General patterns
    "AtOp",
    "ContainsOp",
    "LenOp",
    "SliceOp",
    "DelAttrOp",
    "GetAttrOp",
    "SetAttrOp",
    "ConditionalOp",
    "IsEmptyOp",
    "IsNaNOp",
    "NotEmptyOp",
    "NotNaNOp",
    # type_ — Concrete type methods
    "BytesCountOp",
    "BytesEndsWithOp",
    "BytesFindOp",
    "BytesLowerOp",
    "BytesLStripOp",
    "BytesReplaceOp",
    "BytesRStripOp",
    "BytesSplitOp",
    "BytesStartsWithOp",
    "BytesStripOp",
    "BytesUpperOp",
    "DecodeOp",
    "HexOp",
    "CapitalizeOp",
    "CenterOp",
    "CountSubstringOp",
    "EncodeOp",
    "EndsWithOp",
    "IsAlnumOp",
    "IsAlphaOp",
    "IsDigitOp",
    "IsSpaceOp",
    "LJustOp",
    "LStripOp",
    "LowerOp",
    "RJustOp",
    "RSplitOp",
    "RStripOp",
    "ReplaceOp",
    "SplitOp",
    "StartsWithOp",
    "StrFindOp",
    "StrRFindOp",
    "StrStripOp",
    "SwapCaseOp",
    "TitleOp",
    "UpperOp",
    "ZFillOp",
    # abc_ — ABC-level operations + commands
    # Sequence
    "FirstOp",
    "LastOp",
    "IndexOfOp",
    "CountOp",
    "AppendCmd",
    "ExtendCmd",
    "InsertCmd",
    "PopCmd",
    "RemoveValueCmd",
    # Mapping
    "KeysOp",
    "ValuesOp",
    "ItemsOp",
    "GetOp",
    "SetItemCmd",
    "DeleteItemCmd",
    "UpdateCmd",
    # Set
    "UnionOp",
    "IntersectionOp",
    "DifferenceOp",
    "SymmetricDifferenceOp",
    "IsSubsetOp",
    "IsSupersetOp",
    "IsDisjointOp",
    "AddCmd",
    "RemoveCmd",
    "DiscardCmd",
    # Shared
    "ClearCmd",
]
