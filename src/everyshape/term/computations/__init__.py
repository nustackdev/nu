"""Computations - operations and commands for shape system."""

from __future__ import annotations

# Binary operations
from .binary_ops import (
    AddOp,
    AndOp,
    BitwiseAndOp,
    BitwiseOrOp,
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
    NeOp,
    OrOp,
    PowOp,
    RShiftOp,
    SubOp,
    XorOp,
)

# Bytes operations
from .bytes_ops import (
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

# Commands
from .commands import (
    AddCmd,
    AppendCmd,
    ClearCmd,
    DeleteCmd,
    DiscardCmd,
    InsertCmd,
    PopCmd,
    RemoveCmd,
    SetCmd,
    StoreCmd,
)

# Conversion operations
from .conversion_ops import (
    ConversionOp,
    ToBoolOp,
    ToBytesOp,
    ToFloatOp,
    ToIntOp,
    ToListOp,
    ToSetOp,
    ToStrOp,
    ToTupleOp,
)

# Mapping operations
from .mapping_ops import (
    ContainsOp,
    DictGetOp,
    DictItemsOp,
    DictKeysOp,
    DictValuesOp,
)

# Reactive operations
from .reactive_ops import (
    ChangeOp,
    OnChangeOp,
    OnChildChangeOp,
    OnChildrenChangeOp,
    OnDescendantsChangeOp,
    OnPrimitiveChangeOp,
)

# Ref operations
from .ref_ops import (
    CountOp,
    ExistsOp,
    ExtractOp,
    FilterItemsOp,
    FilterOp,
    FindIndexOp,
    FindItemOp,
    FindKeyOp,
    FindOp,
    FindValueOp,
    GetOp,
    IndexOp,
    ItemsOp,
    KeysOp,
    LengthOp,
    MapItemsOp,
    MapOp,
    MapValuesOp,
    MissingOp,
    ReduceItemsOp,
    ReduceOp,
    ValuesOp,
)

# Sequence operations
from .sequence_ops import (
    AllOp,
    AnyOp,
    AtOp,
    FirstOp,
    IndexOfOp,
    JoinOp,
    LastOp,
    LenOp,
    MaxOp,
    MinOp,
    ReversedOp,
    SliceOp,
    SortedOp,
    SumOp,
)
from .sequence_ops import CountOp as SeqCountOp
from .sequence_ops import FilterOp as SeqFilterOp
from .sequence_ops import FindIndexOp as SeqFindIndexOp
from .sequence_ops import MapOp as SeqMapOp
from .sequence_ops import ReduceOp as SeqReduceOp

# Set operations
from .set_ops import (
    DifferenceOp,
    IntersectionOp,
    IsDisjointOp,
    IsSubsetOp,
    IsSupersetOp,
    SymmetricDifferenceOp,
    UnionOp,
)

# String operations
from .string_ops import (
    CapitalizeOp,
    CenterOp,
    CountSubstringOp,
    EncodeOp,
    EndsWithOp,
    IsAlnumOp,
    IsAlphaOp,
    IsDigitOp,
    IsSpaceOp,
    LJustOp,
    LowerOp,
    LStripOp,
    ReplaceOp,
    RFindOp,
    RJustOp,
    RSplitOp,
    RStripOp,
    SplitOp,
    StartsWithOp,
    StripOp,
    SwapCaseOp,
    TitleOp,
    UpperOp,
    ZFillOp,
)
from .string_ops import (
    FindOp as StrFindOp,
)

# Ternary operations
from .ternary_ops import ConditionalOp

# TypedVar operations (function/method calls, typed commands)
from .typedval_ops import (
    FuncCallOp,
    MethodCallOp,
    TypedSetCmd,
)

# Unary operations
from .unary_ops import (
    AbsOp,
    BitwiseNotOp,
    BoolOp,
    IsEmptyOp,
    IsNaNOp,
    NegOp,
    NotEmptyOp,
    NotNaNOp,
    NotOp,
    PosOp,
)


__all__ = [  # noqa: RUF022
    # ==========================================================================
    # UNARY OPERATIONS
    # ==========================================================================
    "NegOp",
    "AbsOp",
    "PosOp",
    "NotOp",
    "BitwiseNotOp",
    "BoolOp",
    "IsEmptyOp",
    "NotEmptyOp",
    "IsNaNOp",
    "NotNaNOp",
    # ==========================================================================
    # TYPEDVALUE OPERATIONS
    # ==========================================================================
    "FuncCallOp",
    "MethodCallOp",
    "TypedSetCmd",
    # ==========================================================================
    # CONVERSION OPERATIONS
    # ==========================================================================
    "ConversionOp",
    "ToIntOp",
    "ToFloatOp",
    "ToBoolOp",
    "ToStrOp",
    "ToBytesOp",
    "ToListOp",
    "ToSetOp",
    "ToTupleOp",
    # ==========================================================================
    # BINARY OPERATIONS
    # ==========================================================================
    "AddOp",
    "SubOp",
    "MulOp",
    "DivOp",
    "FloorDivOp",
    "ModOp",
    "PowOp",
    "GtOp",
    "LtOp",
    "GeOp",
    "LeOp",
    "EqOp",
    "NeOp",
    "IdCompOp",
    "AndOp",
    "OrOp",
    "XorOp",
    "LShiftOp",
    "RShiftOp",
    "BitwiseAndOp",
    "BitwiseOrOp",
    # ==========================================================================
    # TERNARY OPERATIONS
    # ==========================================================================
    "ConditionalOp",
    # ==========================================================================
    # SEQUENCE OPERATIONS
    # ==========================================================================
    "LenOp",
    "AtOp",
    "SliceOp",
    "FirstOp",
    "LastOp",
    "SumOp",
    "MinOp",
    "MaxOp",
    "SortedOp",
    "ReversedOp",
    "AnyOp",
    "AllOp",
    "JoinOp",
    "SeqMapOp",
    "SeqFilterOp",
    "SeqReduceOp",
    "SeqCountOp",
    "IndexOfOp",
    "SeqFindIndexOp",
    # ==========================================================================
    # MAPPING OPERATIONS
    # ==========================================================================
    "ContainsOp",
    "DictKeysOp",
    "DictValuesOp",
    "DictItemsOp",
    "DictGetOp",
    # ==========================================================================
    # STRING OPERATIONS
    # ==========================================================================
    "UpperOp",
    "LowerOp",
    "TitleOp",
    "CapitalizeOp",
    "SwapCaseOp",
    "StripOp",
    "LStripOp",
    "RStripOp",
    "SplitOp",
    "RSplitOp",
    "StrFindOp",
    "RFindOp",
    "CountSubstringOp",
    "StartsWithOp",
    "EndsWithOp",
    "IsDigitOp",
    "IsAlphaOp",
    "IsAlnumOp",
    "IsSpaceOp",
    "CenterOp",
    "LJustOp",
    "RJustOp",
    "ZFillOp",
    "ReplaceOp",
    "EncodeOp",
    # ==========================================================================
    # BYTES OPERATIONS
    # ==========================================================================
    "DecodeOp",
    "HexOp",
    "BytesUpperOp",
    "BytesLowerOp",
    "BytesStripOp",
    "BytesLStripOp",
    "BytesRStripOp",
    "BytesSplitOp",
    "BytesFindOp",
    "BytesCountOp",
    "BytesStartsWithOp",
    "BytesEndsWithOp",
    "BytesReplaceOp",
    # ==========================================================================
    # SET OPERATIONS
    # ==========================================================================
    "UnionOp",
    "IntersectionOp",
    "DifferenceOp",
    "SymmetricDifferenceOp",
    "IsSubsetOp",
    "IsSupersetOp",
    "IsDisjointOp",
    # ==========================================================================
    # REF OPERATIONS
    # ==========================================================================
    "GetOp",
    "ExtractOp",
    "ExistsOp",
    "MissingOp",
    "LengthOp",
    "MapOp",
    "FilterOp",
    "ReduceOp",
    "IndexOp",
    "CountOp",
    "FindOp",
    "FindIndexOp",
    "KeysOp",
    "ValuesOp",
    "ItemsOp",
    "MapValuesOp",
    "MapItemsOp",
    "FilterItemsOp",
    "ReduceItemsOp",
    "FindKeyOp",
    "FindValueOp",
    "FindItemOp",
    # ==========================================================================
    # REACTIVE OPERATIONS
    # ==========================================================================
    "ChangeOp",
    "OnChangeOp",
    "OnChildChangeOp",
    "OnChildrenChangeOp",
    "OnDescendantsChangeOp",
    "OnPrimitiveChangeOp",
    # ==========================================================================
    # COMMANDS
    # ==========================================================================
    "SetCmd",
    "DeleteCmd",
    "StoreCmd",
    "ClearCmd",
    "AppendCmd",
    "InsertCmd",
    "PopCmd",
    "AddCmd",
    "RemoveCmd",
    "DiscardCmd",
]
