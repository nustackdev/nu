"""Concrete morphisms for everybase.

Structure:
- arithmetic.py: NegOp, AbsOp, PosOp, AddOp, SubOp, MulOp, DivOp, etc.
- comparison.py: EqOp, NeOp, GtOp, LtOp, GeOp, LeOp, IdCompOp
- logical.py: NotOp, BoolOp, AndOp, OrOp
- bitwise.py: BitwiseNotOp, BitwiseAndOp, BitwiseOrOp, XorOp, LShiftOp, RShiftOp
- conversion.py: ToIntOp, ToStrOp, ToBoolOp, ToFloatOp, ToBytesOp, etc.
- special.py: IsEmptyOp, IsNaNOp, NotEmptyOp, NotNaNOp
- conditional.py: ConditionalOp
- callable.py: FuncCallOp, MethodCallOp, GetAttrOp, SetAttrOp, DelAttrOp
- collection_access.py: AtOp, SliceOp, LenOp, ContainsOp
- collection_aggregate.py: SumOp, MinOp, MaxOp, AnyOp, AllOp
- collection_search.py: FirstOp, LastOp, IndexOfOp, FindOp, FindIndexOp, CountOp, JoinOp
- collection_transform.py: MapOp, FilterOp, ReduceOp, SortedOp, ReversedOp
- bytes_ops.py: Bytes-specific ops (DecodeOp, HexOp, etc.)
- str_ops.py: String-specific ops (UpperOp, SplitOp, etc.)
- dict_ops.py: Dict-specific ops (DictKeysOp, DictValuesOp, etc.)
- set_ops.py: Set-specific ops (UnionOp, IntersectionOp, etc.)

All morphisms use every.Morphism base classes and implement apply().
"""

# Arithmetic
from .arithmetic import (
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

# Bitwise
from .bitwise import (
    BitwiseAndOp,
    BitwiseNotOp,
    BitwiseOrOp,
    LShiftOp,
    RShiftOp,
    XorOp,
)

# Bytes ops
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

# Callable (function/method invocation)
from .callable import DelAttrOp, FuncCallOp, GetAttrOp, MethodCallOp, SetAttrOp

# Collection ops - access
from .collection_access import (
    AtOp,
    ContainsOp,
    LenOp,
    SliceOp,
)

# Collection ops - aggregate
from .collection_aggregate import (
    AllOp,
    AnyOp,
    MaxOp,
    MinOp,
    SumOp,
)

# Collection ops - search
from .collection_search import (
    CountOp,
    FindIndexOp,
    FindOp,
    FirstOp,
    IndexOfOp,
    JoinOp,
    LastOp,
)

# Collection ops - transform
from .collection_transform import (
    FilterOp,
    MapOp,
    ReduceOp,
    ReversedOp,
    SortedOp,
)

# Comparison
from .comparison import EqOp, GeOp, GtOp, IdCompOp, LeOp, LtOp, NeOp

# Conditional
from .conditional import ConditionalOp

# Conversion
from .conversion import (
    ToBoolOp,
    ToBytesOp,
    ToFloatOp,
    ToIntOp,
    ToListOp,
    ToSetOp,
    ToStrOp,
    ToTupleOp,
)

# Dict ops
from .dict_ops import (
    DictGetOp,
    DictItemsOp,
    DictKeysOp,
    DictValuesOp,
)

# Logical
from .logical import AndOp, BoolOp, NotOp, OrOp

# Set ops
from .set_ops import (
    DifferenceOp,
    IntersectionOp,
    IsDisjointOp,
    IsSubsetOp,
    IsSupersetOp,
    SymmetricDifferenceOp,
    UnionOp,
)

# Special value checks
from .special import IsEmptyOp, IsNaNOp, NotEmptyOp, NotNaNOp

# String ops
from .str_ops import (
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
from .str_ops import (
    FindOp as StrFindOp,
)
from .str_ops import (
    RFindOp as StrRFindOp,
)
from .str_ops import (
    StripOp as StrStripOp,
)


__all__ = [  # noqa: RUF022
    # Arithmetic
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
    # Comparison
    "EqOp",
    "GeOp",
    "GtOp",
    "IdCompOp",
    "LeOp",
    "LtOp",
    "NeOp",
    # Logical
    "AndOp",
    "BoolOp",
    "NotOp",
    "OrOp",
    # Bitwise
    "BitwiseAndOp",
    "BitwiseNotOp",
    "BitwiseOrOp",
    "LShiftOp",
    "RShiftOp",
    "XorOp",
    # Conversion
    "ToBoolOp",
    "ToBytesOp",
    "ToFloatOp",
    "ToIntOp",
    "ToListOp",
    "ToSetOp",
    "ToStrOp",
    "ToTupleOp",
    # Special
    "IsEmptyOp",
    "IsNaNOp",
    "NotEmptyOp",
    "NotNaNOp",
    # Conditional
    "ConditionalOp",
    # Callable
    "DelAttrOp",
    "FuncCallOp",
    "GetAttrOp",
    "MethodCallOp",
    "SetAttrOp",
    # Collection
    "AllOp",
    "AnyOp",
    "AtOp",
    "ContainsOp",
    "CountOp",
    "FilterOp",
    "FindIndexOp",
    "FindOp",
    "FirstOp",
    "IndexOfOp",
    "JoinOp",
    "LastOp",
    "LenOp",
    "MapOp",
    "MaxOp",
    "MinOp",
    "ReduceOp",
    "ReversedOp",
    "SliceOp",
    "SortedOp",
    "SumOp",
    # Bytes
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
    # String
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
    # Dict
    "DictGetOp",
    "DictItemsOp",
    "DictKeysOp",
    "DictValuesOp",
    # Set
    "DifferenceOp",
    "IntersectionOp",
    "IsDisjointOp",
    "IsSubsetOp",
    "IsSupersetOp",
    "SymmetricDifferenceOp",
    "UnionOp",
]
