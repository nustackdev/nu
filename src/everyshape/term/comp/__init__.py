# """Computations module - operations and commands for the term layer.

# This module provides all computation operations organized by domain:

# Submodules:
# - bases: Foundation tier (UnaryOp, BinaryOp, TernaryOp base classes)
# - value: Value operations (arithmetic, comparison, logical, conversion)
# - types: Type-specific operations (string, bytes, sequence, mapping, set)
# - ref: Reference operations (access, mutate, sequence, mapping, set)
# - reactive: Reactive operations (OnChangeOp, etc.)
# - typed: TypedValue operations (FuncCallOp, MethodCallOp, etc.)

# Top-level exports:
# - Ref operations (MapOp, FilterOp, etc.) work on LValue references
# - Type operations from types/ (sequence, string, etc.) work on RValues
# - For sequence value operations, import from comps.types.sequence directly

# Note on duplicate names:
# - MapOp, FilterOp, ReduceOp at top-level are REF operations (lazy, storage)
# - types.sequence has equivalent ops for SEQUENCE VALUES (eager, in-memory)
# - Use fully-qualified imports when you need the sequence value versions:
#     from everyshape.term.comps.types.sequence import MapOp as SeqMapOp
# """


# """Type-specific operations module.

# Re-exports from:
# - string: String operations (UpperOp, LowerOp, etc.)
# - bytes: Bytes operations (DecodeOp, HexOp, etc.)
# - sequence: Sequence operations (SumOp, MinOp, etc.)
# - mapping: Mapping operations (DictKeysOp, DictTypesOp, etc.)
# - set: Set operations (UnionOp, IntersectionOp, etc.)
# """

# from .bytes import (
#     BytesCountOp,
#     BytesEndsWithOp,
#     BytesFindOp,
#     BytesLowerOp,
#     BytesLStripOp,
#     BytesReplaceOp,
#     BytesRStripOp,
#     BytesSplitOp,
#     BytesStartsWithOp,
#     BytesStripOp,
#     BytesUpperOp,
#     DecodeOp,
#     HexOp,
# )
# from .mapping import (
#     ContainsOp,
#     DictGetOp,
#     DictItemsOp,
#     DictKeysOp,
#     DictTypesOp,
# )
# from .sequence import (
#     AllOp,
#     AnyOp,
#     AtOp,
#     CountOp,
#     FilterOp,
#     FindIndexOp,
#     FindOp,
#     FirstOp,
#     IndexOfOp,
#     JoinOp,
#     LastOp,
#     LenOp,
#     MapOp,
#     MaxOp,
#     MinOp,
#     ReduceOp,
#     ReversedOp,
#     SliceOp,
#     SortedOp,
#     SumOp,
# )
# from .set import (
#     DifferenceOp,
#     IntersectionOp,
#     IsDisjointOp,
#     IsSubsetOp,
#     IsSupersetOp,
#     SymmetricDifferenceOp,
#     UnionOp,
# )
# from .string import (
#     CapitalizeOp,
#     CenterOp,
#     CountSubstringOp,
#     EncodeOp,
#     EndsWithOp,
#     IsAlnumOp,
#     IsAlphaOp,
#     IsDigitOp,
#     IsSpaceOp,
#     LJustOp,
#     LowerOp,
#     LStripOp,
#     ReplaceOp,
#     RFindOp,
#     RJustOp,
#     RSplitOp,
#     RStripOp,
#     SplitOp,
#     StartsWithOp,
#     StripOp,
#     SwapCaseOp,
#     TitleOp,
#     UpperOp,
#     ZFillOp,
# )
# from .string import (
#     FindOp as StringFindOp,
# )


# __all__ = [
#     # Sequence ops
#     "AllOp",
#     "AnyOp",
#     "AtOp",
#     # Bytes ops
#     "BytesCountOp",
#     "BytesEndsWithOp",
#     "BytesFindOp",
#     "BytesLStripOp",
#     "BytesLowerOp",
#     "BytesRStripOp",
#     "BytesReplaceOp",
#     "BytesSplitOp",
#     "BytesStartsWithOp",
#     "BytesStripOp",
#     "BytesUpperOp",
#     # String ops
#     "CapitalizeOp",
#     "CenterOp",
#     # Mapping ops
#     "ContainsOp",
#     "CountOp",
#     "CountSubstringOp",
#     "DecodeOp",
#     "DictGetOp",
#     "DictItemsOp",
#     "DictKeysOp",
#     "DictTypesOp",
#     # Set ops
#     "DifferenceOp",
#     "EncodeOp",
#     "EndsWithOp",
#     "FilterOp",
#     "FindIndexOp",
#     "FindOp",
#     "FirstOp",
#     "HexOp",
#     "IndexOfOp",
#     "IntersectionOp",
#     "IsAlnumOp",
#     "IsAlphaOp",
#     "IsDigitOp",
#     "IsDisjointOp",
#     "IsSpaceOp",
#     "IsSubsetOp",
#     "IsSupersetOp",
#     "JoinOp",
#     "LJustOp",
#     "LStripOp",
#     "LastOp",
#     "LenOp",
#     "LowerOp",
#     "MapOp",
#     "MaxOp",
#     "MinOp",
#     "RFindOp",
#     "RJustOp",
#     "RSplitOp",
#     "RStripOp",
#     "ReduceOp",
#     "ReplaceOp",
#     "ReversedOp",
#     "SliceOp",
#     "SortedOp",
#     "SplitOp",
#     "StartsWithOp",
#     "StringFindOp",
#     "StripOp",
#     "SumOp",
#     "SwapCaseOp",
#     "SymmetricDifferenceOp",
#     "TitleOp",
#     "UnionOp",
#     "UpperOp",
#     "ZFillOp",
# ]

# """Value operations module.

# Re-exports from:
# - unary_ops: Unary operations (NegOp, AbsOp, etc.)
# - binary_ops: Binary operations (AddOp, SubOp, etc.)
# - ternary_ops: Ternary operations (ConditionalOp, etc.)
# - conversion: Type conversion operations (ToIntOp, ToStrOp, etc.)
# """

# from .binary_ops import (
#     AddOp,
#     AndOp,
#     BinaryOp,
#     BitwiseAndOp,
#     BitwiseOrOp,
#     DivOp,
#     EqOp,
#     FloorDivOp,
#     GeOp,
#     GtOp,
#     IdCompOp,
#     LeOp,
#     LShiftOp,
#     LtOp,
#     ModOp,
#     MulOp,
#     NeOp,
#     OrOp,
#     PowOp,
#     RShiftOp,
#     SubOp,
#     XorOp,
# )
# from .conversion_ops import (
#     ConversionOp,
#     ToBoolOp,
#     ToBytesOp,
#     ToFloatOp,
#     ToIntOp,
#     ToListOp,
#     ToSetOp,
#     ToStrOp,
#     ToTupleOp,
# )
# from .ternary_ops import (
#     ConditionalOp,
#     TernaryOp,
# )
# from .unary_ops import (
#     AbsOp,
#     BitwiseNotOp,
#     BoolOp,
#     IsEmptyOp,
#     IsNaNOp,
#     NegOp,
#     NotEmptyOp,
#     NotNaNOp,
#     NotOp,
#     PosOp,
#     UnaryOp,
# )


# __all__ = [
#     # Unary ops
#     "AbsOp",
#     # Binary ops
#     "AddOp",
#     "AndOp",
#     "BinaryOp",
#     "BitwiseAndOp",
#     "BitwiseNotOp",
#     "BitwiseOrOp",
#     "BoolOp",
#     # Ternary ops
#     "ConditionalOp",
#     # Conversion ops
#     "ConversionOp",
#     "DivOp",
#     "EqOp",
#     "FloorDivOp",
#     "GeOp",
#     "GtOp",
#     "IdCompOp",
#     "IsEmptyOp",
#     "IsNaNOp",
#     "LShiftOp",
#     "LeOp",
#     "LtOp",
#     "ModOp",
#     "MulOp",
#     "NeOp",
#     "NegOp",
#     "NotEmptyOp",
#     "NotNaNOp",
#     "NotOp",
#     "OrOp",
#     "PosOp",
#     "PowOp",
#     "RShiftOp",
#     "SubOp",
#     "TernaryOp",
#     "ToBoolOp",
#     "ToBytesOp",
#     "ToFloatOp",
#     "ToIntOp",
#     "ToListOp",
#     "ToSetOp",
#     "ToStrOp",
#     "ToTupleOp",
#     "UnaryOp",
#     "XorOp",
# ]
"""INIT :)."""
