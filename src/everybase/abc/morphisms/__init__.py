"""Concrete morphisms for everybase.

Structure:

operator/     — Python operators (syntactic)
  arithmetic.py: NegOp, AbsOp, PosOp, AddOp, SubOp, MulOp, DivOp, FloorDivOp, ModOp, PowOp
  comparison.py: EqOp, NeOp, GtOp, LtOp, GeOp, LeOp, IdCompOp
  logical.py: NotOp, BoolOp, AndOp, OrOp
  bitwise.py: BitwiseNotOp, BitwiseAndOp, BitwiseOrOp, XorOp, LShiftOp, RShiftOp

itertools/    — Higher-order & iteration
  transform.py: MapOp, FilterOp, SortedOp, ReversedOp, PluckOp, ToDictOp, FilterByOp, FlattenOp, UniqueOp
  combine.py: ZipOp, ChainOp, EnumerateOp
  slice.py: TakeOp, DropOp
  group.py: GroupByOp, PartitionOp
  reduce.py: ReduceOp, SumOp, MinOp, MaxOp, AnyOp, AllOp
  search.py: FindOp, FindIndexOp

builtins/     — General patterns & conversions
  access.py: AtOp, SliceOp, LenOp, ContainsOp
  attr.py: GetAttrOp, SetAttrOp, DelAttrOp
  call.py: FuncCall/Op/Cmd, MethodCall/Op/Cmd
  conversion.py: ToIntOp, ToStrOp, ToBoolOp, ToFloatOp, ToBytesOp, ToListOp, ToSetOp, ToTupleOp
  special.py: IsEmptyOp, IsNaNOp, NotEmptyOp, NotNaNOp

collections/  — Collection structural ops & commands
  sequence.py: FirstOp, LastOp, IndexOfOp, CountOp, AppendCmd, ExtendCmd, InsertCmd, PopCmd, RemoveValueCmd
  mapping.py: KeysOp, ValuesOp, ItemsOp, GetOp, KeyAtOp, ISliceOp, SetItemCmd, DeleteItemCmd, UpdateCmd
  set.py: UnionOp...DiscardCmd
  shared.py: ClearCmd

str_.py       — String-specific ops (UpperOp, SplitOp, JoinOp, etc.)
bytes_.py     — Bytes-specific ops (DecodeOp, HexOp, etc.)

All morphisms use every.Morphism base classes and implement apply().
"""

# ── operator/ — Python operators ─────────────────────────────────────────────
# ── builtins/ — General patterns & conversions ───────────────────────────────
from .builtins import (
    AtOp,
    ContainsOp,
    DelAttrOp,
    FuncCall,
    FuncCallCmd,
    FuncCallOp,
    GetAttrOp,
    IsEmptyOp,
    IsNaNOp,
    LenOp,
    MethodCall,
    MethodCallCmd,
    MethodCallOp,
    NotEmptyOp,
    NotNaNOp,
    SetAttrOp,
    SliceOp,
    ToBoolOp,
    ToBytesOp,
    ToFloatOp,
    ToIntOp,
    ToListOp,
    ToSetOp,
    ToStrOp,
    ToTupleOp,
)

# ── str/bytes — Type-specific ops ────────────────────────────────────────────
from .bytes_ import (
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

# ── collections/ — Collection structural ops & commands ──────────────────────
from .collections import (
    AddCmd,
    AppendCmd,
    ClearCmd,
    CountOp,
    DeleteItemCmd,
    DifferenceOp,
    DiscardCmd,
    ExtendCmd,
    FirstOp,
    GetOp,
    IndexOfOp,
    InsertCmd,
    IntersectionOp,
    IsDisjointOp,
    ISliceOp,
    IsSubsetOp,
    IsSupersetOp,
    ItemsOp,
    KeyAtOp,
    KeysOp,
    LastOp,
    PopCmd,
    RemoveCmd,
    RemoveValueCmd,
    SetItemCmd,
    SymmetricDifferenceOp,
    UnionOp,
    UpdateCmd,
    ValuesOp,
)

# ── itertools/ — Higher-order & iteration ────────────────────────────────────
from .itertools import (
    AllOp,
    AnyOp,
    ChainOp,
    DropOp,
    EnumerateOp,
    FilterByOp,
    FilterOp,
    FindIndexOp,
    FindOp,
    FlattenOp,
    GroupByOp,
    MapOp,
    MaxOp,
    MinOp,
    PartitionOp,
    PluckOp,
    ReduceOp,
    ReversedOp,
    SortedOp,
    SumOp,
    TakeOp,
    ToDictOp,
    UniqueOp,
    ZipOp,
)
from .operator import (
    AbsOp,
    AddOp,
    AndOp,
    BitwiseAndOp,
    BitwiseNotOp,
    BitwiseOrOp,
    BoolOp,
    DivOp,
    EqOp,
    FloorDivOp,
    GeOp,
    GtOp,
    IdCompOp,
    LeOp,
    LShiftOp,
    LtOp,
    ModOp,
    MulOp,
    NegOp,
    NeOp,
    NotOp,
    OrOp,
    PosOp,
    PowOp,
    RShiftOp,
    SubOp,
    XorOp,
)
from .str_ import (
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
from .str_ import (
    FindOp as StrFindOp,
)
from .str_ import (
    RFindOp as StrRFindOp,
)
from .str_ import (
    StripOp as StrStripOp,
)


__all__ = [  # noqa: RUF022
    # operator/ — Python operators
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
    # itertools/ — Higher-order & iteration
    "AllOp",
    "AnyOp",
    "MaxOp",
    "MinOp",
    "SumOp",
    "FilterByOp",
    "FilterOp",
    "MapOp",
    "PluckOp",
    "ReduceOp",
    "ReversedOp",
    "SortedOp",
    "ToDictOp",
    "FlattenOp",
    "UniqueOp",
    "ChainOp",
    "DropOp",
    "EnumerateOp",
    "GroupByOp",
    "PartitionOp",
    "TakeOp",
    "ZipOp",
    "FindOp",
    "FindIndexOp",
    # builtins/ — General patterns & conversions
    "AtOp",
    "ContainsOp",
    "LenOp",
    "SliceOp",
    "DelAttrOp",
    "GetAttrOp",
    "SetAttrOp",
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
    "IsEmptyOp",
    "IsNaNOp",
    "NotEmptyOp",
    "NotNaNOp",
    # collections/ — Collection structural ops & commands
    "FirstOp",
    "LastOp",
    "IndexOfOp",
    "CountOp",
    "AppendCmd",
    "ExtendCmd",
    "InsertCmd",
    "PopCmd",
    "RemoveValueCmd",
    "KeysOp",
    "ValuesOp",
    "ItemsOp",
    "GetOp",
    "KeyAtOp",
    "ISliceOp",
    "SetItemCmd",
    "DeleteItemCmd",
    "UpdateCmd",
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
    "ClearCmd",
    # str/bytes — Type-specific ops
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
    "JoinOp",
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
]
