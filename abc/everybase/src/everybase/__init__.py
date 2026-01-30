"""Everybase - Foundation library for the every ecosystem.

Structure:
- capabilities/: Capability mixins for refs (Numeric, Comparable, Logical, etc.)
- protocols/: Storage capability protocols (Gettable, Settable, etc.)
- morphisms/: Concrete morphisms (AddOp, SubOp, EqOp, etc.)
- refs/: Abstract ref bases (IntRefBase, StrRefBase, etc.)
- py/: Python memory refs (IntRef, StrRef, ListRef, etc.)
- util/: Utilities (ensure_term, typed_ref, combiners)
"""

# Re-export traits
# Re-export morphisms
from everybase.capabilities import (
    Addable,
    Additive,
    Andable,
    Bitwise,
    BitwiseAndable,
    BitwiseInvertable,
    BitwiseOrable,
    BitwiseXorable,
    Comparable,
    Containable,
    Divisible,
    Equalable,
    Indexable,
    Iterable,
    Lengthable,
    Logical,
    Mapping,
    Moduloable,
    Multiplicative,
    Multiplyable,
    Negatable,
    Notable,
    Numeric,
    Orable,
    Orderable,
    Powerable,
    Sequence,
    SetLike,
    Shiftable,
    Sliceable,
    Subtractable,
)
from everybase.morphisms import (
    # Arithmetic
    AbsOp,
    AddOp,
    # Collection
    AllOp,
    # Logical
    AndOp,
    AnyOp,
    AtOp,
    # Bitwise
    BitwiseAndOp,
    BitwiseNotOp,
    BitwiseOrOp,
    BoolOp,
    # Conditional
    ConditionalOp,
    ContainsOp,
    CountOp,
    # Callable
    DelAttrOp,
    DivOp,
    # Comparison
    EqOp,
    FilterOp,
    FindIndexOp,
    FindOp,
    FirstOp,
    FloorDivOp,
    FuncCallOp,
    GeOp,
    GetAttrOp,
    GtOp,
    IdCompOp,
    IndexOfOp,
    # Special
    IsEmptyOp,
    IsNaNOp,
    JoinOp,
    LastOp,
    LenOp,
    LeOp,
    LShiftOp,
    LtOp,
    MapOp,
    MaxOp,
    MethodCallOp,
    MinOp,
    ModOp,
    MulOp,
    NegOp,
    NeOp,
    NotEmptyOp,
    NotNaNOp,
    NotOp,
    OrOp,
    PosOp,
    PowOp,
    ReduceOp,
    ReversedOp,
    RShiftOp,
    SetAttrOp,
    SliceOp,
    SortedOp,
    SubOp,
    SumOp,
    # Conversion
    ToBoolOp,
    ToBytesOp,
    ToFloatOp,
    ToIntOp,
    ToListOp,
    ToSetOp,
    ToStrOp,
    ToTupleOp,
    XorOp,
)

# Re-export protocols
from everybase.protocols import (
    # Capability protocols
    Appendable,
    Clearable,
    # Collection protocols
    CollectionItemRef,
    CollectionRef,
    ContainerRef,
    Deletable,
    Existable,
    Extractable,
    Gettable,
    Insertable,
    ItemsQueryable,
    KeysQueryable,
    MappingAccessible,
    MappingRef,
    MutableMappingRef,
    MutableSequenceRef,
    MutableSetLikeRef,
    Nestable,
    Poppable,
    RefChildObservable,
    RefDescendantsObservable,
    RefIndexable,
    RefObservable,
    RefSliceable,
    SequenceRef,
    SetLikeRef,
    Settable,
    Storable,
    ValuesQueryable,
    # Type guards
    is_clearable,
    is_deletable,
    is_existable,
    is_extractable,
    is_gettable,
    is_lengthable,
    is_mapping_accessible,
    is_ref_indexable,
    is_ref_observable,
    is_settable,
    is_storable,
)

# Re-export py refs
from everybase.py import (
    AnyRef,
    BoolRef,
    BytesRef,
    DictRef,
    EmptyRef,
    FloatRef,
    FrozenSetRef,
    IntRef,
    InvalidRef,
    ListRef,
    NoneRef,
    PyRefBase,
    SentinelRef,
    SetRef,
    StrRef,
    TupleRef,
)
from everybase.py import (
    SetRef as PySetRef,  # Avoid collision with SetRef protocol
)

# Re-export ref bases
from everybase.refs import (
    AnyRefBase,
    BoolRefBase,
    BytesRefBase,
    DictRefBase,
    EmptyRefBase,
    FloatRefBase,
    FrozenSetRefBase,
    IntRefBase,
    InvalidRefBase,
    ListRefBase,
    NoneRefBase,
    RefBase,
    SentinelRefBase,
    SetRefBase,
    StrRefBase,
    TupleRefBase,
)

# Re-export utilities
from everybase.util import (
    all_,
    and_,
    any_,
    coalesce,
    ensure_term,
    ifelse,
    none_,
    or_,
    typed_ref,
)


__all__ = [  # noqa: RUF022
    # =========================================================================
    # CAPABILITIES (operator + collection mixins)
    # =========================================================================
    # Arithmetic
    "Addable",
    "Subtractable",
    "Negatable",
    "Multiplyable",
    "Divisible",
    "Moduloable",
    "Powerable",
    "Additive",
    "Multiplicative",
    "Numeric",
    # Comparison
    "Orderable",
    "Equalable",
    "Comparable",
    # Logical
    "Andable",
    "Orable",
    "Notable",
    "Logical",
    # Bitwise
    "BitwiseAndable",
    "BitwiseOrable",
    "BitwiseXorable",
    "BitwiseInvertable",
    "Shiftable",
    "Bitwise",
    # Collection
    "Lengthable",
    "Indexable",
    "Sliceable",
    "Containable",
    "Iterable",
    "Sequence",
    "Mapping",
    "SetLike",
    # =========================================================================
    # PROTOCOLS (storage capabilities)
    # =========================================================================
    # Read
    "Gettable",
    "Extractable",
    # Write
    "Settable",
    "Storable",
    "Appendable",
    "Insertable",
    # Delete
    "Deletable",
    "Clearable",
    "Poppable",
    # Existence
    "Existable",
    # Observable
    "RefObservable",
    "RefChildObservable",
    "RefDescendantsObservable",
    # Navigation
    "Nestable",
    "RefIndexable",
    "RefSliceable",
    # Query
    "KeysQueryable",
    "ValuesQueryable",
    "ItemsQueryable",
    # Mapping access
    "MappingAccessible",
    # Type guards
    "is_gettable",
    "is_extractable",
    "is_settable",
    "is_storable",
    "is_deletable",
    "is_clearable",
    "is_existable",
    "is_ref_observable",
    "is_ref_indexable",
    "is_lengthable",
    "is_mapping_accessible",
    # Collection protocols
    "ContainerRef",
    "CollectionRef",
    "SequenceRef",
    "MutableSequenceRef",
    "MappingRef",
    "MutableMappingRef",
    "SetLikeRef",
    "MutableSetLikeRef",
    "CollectionItemRef",
    # =========================================================================
    # MORPHISMS (operations)
    # =========================================================================
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
    # =========================================================================
    # REFS (Python memory)
    # =========================================================================
    "PyRefBase",
    "IntRef",
    "FloatRef",
    "BoolRef",
    "StrRef",
    "BytesRef",
    "ListRef",
    "SetRef",
    "DictRef",
    "PySetRef",
    "FrozenSetRef",
    "TupleRef",
    "AnyRef",
    "NoneRef",
    "SentinelRef",
    "EmptyRef",
    "InvalidRef",
    # =========================================================================
    # REF BASES (abstract)
    # =========================================================================
    "RefBase",
    "IntRefBase",
    "FloatRefBase",
    "BoolRefBase",
    "StrRefBase",
    "BytesRefBase",
    "ListRefBase",
    "DictRefBase",
    "SetRefBase",
    "FrozenSetRefBase",
    "TupleRefBase",
    "AnyRefBase",
    "NoneRefBase",
    "SentinelRefBase",
    "EmptyRefBase",
    "InvalidRefBase",
    # =========================================================================
    # UTILITIES
    # =========================================================================
    "ensure_term",
    "typed_ref",
    "all_",
    "and_",
    "any_",
    "or_",
    "coalesce",
    "ifelse",
    "none_",
]
