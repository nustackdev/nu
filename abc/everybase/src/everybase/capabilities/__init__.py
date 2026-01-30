"""Capability protocols and bases for refs.

Each capability has a paired Protocol (structural type contract) and Base (mixin implementation).
Protocols declare the public interface; Bases provide morphism-wrapping implementations.

    GENERAL OPERATIONS (gen_*)
    ──────────────────────────
    Arithmetic:  AddableBase/Protocol … NumericBase/Protocol
    Comparison:  OrderableBase/Protocol, EqualableBase/Protocol, ComparableBase/Protocol
    Logical:     AndableBase/Protocol … LogicalBase/Protocol
    Bitwise:     BitwiseAndableBase/Protocol … BitwiseBase/Protocol

    COLLECTION OPERATIONS (col_*)
    ─────────────────────────────
    Atoms:       ContainableBase/Protocol, LengthableBase/Protocol, IndexableBase/Protocol, SliceableBase/Protocol
    Iterable:    IterableBase/Protocol
    Collection:  CollectionBase/Protocol       = Containable + Lengthable + Iterable
    Sequence:    SequenceBase/Protocol         = Collection + Sliceable + first/last/sorted/...
      Mutable:   MutableSequenceBase/Protocol = Sequence + append/insert/pop
    Mapping:     MappingBase/Protocol          = Collection + keys_/values_/items_/get_
      Mutable:   MutableMappingBase/Protocol  = Mapping + set_/delete/update_
    SetLike:     SetLikeBase/Protocol          = Collection + union/intersection/difference/...
      Mutable:   MutableSetBase/Protocol      = SetLike + add/remove/discard
    Clearable:   ClearableBase/Protocol        = clear()
"""

from .col_atoms import (
    ContainableBase,
    ContainableProtocol,
    IndexableBase,
    IndexableProtocol,
    LengthableBase,
    LengthableProtocol,
    SliceableBase,
    SliceableProtocol,
)
from .col_collection import (
    ClearableBase,
    ClearableProtocol,
    CollectionBase,
    CollectionProtocol,
)
from .col_iterable import (
    IterableBase,
    IterableProtocol,
)
from .col_mapping import (
    MappingBase,
    MappingProtocol,
    MutableMappingBase,
    MutableMappingProtocol,
)
from .col_sequence import (
    MutableSequenceBase,
    MutableSequenceProtocol,
    SequenceBase,
    SequenceProtocol,
)
from .col_set import (
    MutableSetBase,
    MutableSetProtocol,
    SetLikeBase,
    SetLikeProtocol,
)
from .gen_arithmetic import (
    AddableBase,
    AddableProtocol,
    AdditiveBase,
    AdditiveProtocol,
    DivisibleBase,
    DivisibleProtocol,
    ModuloableBase,
    ModuloableProtocol,
    MultiplicativeBase,
    MultiplicativeProtocol,
    MultiplyableBase,
    MultiplyableProtocol,
    NegatableBase,
    NegatableProtocol,
    NumericBase,
    NumericProtocol,
    PowerableBase,
    PowerableProtocol,
    SubtractableBase,
    SubtractableProtocol,
)
from .gen_bitwise import (
    BitwiseAndableBase,
    BitwiseAndableProtocol,
    BitwiseBase,
    BitwiseInvertableBase,
    BitwiseInvertableProtocol,
    BitwiseOrableBase,
    BitwiseOrableProtocol,
    BitwiseProtocol,
    BitwiseXorableBase,
    BitwiseXorableProtocol,
    ShiftableBase,
    ShiftableProtocol,
)
from .gen_comparison import (
    ComparableBase,
    ComparableProtocol,
    EqualableBase,
    EqualableProtocol,
    OrderableBase,
    OrderableProtocol,
)
from .gen_logical import (
    AndableBase,
    AndableProtocol,
    LogicalBase,
    LogicalProtocol,
    NotableBase,
    NotableProtocol,
    OrableBase,
    OrableProtocol,
)
from .loc import (
    LocationDeletableProtocol,
    LocationExistableProtocol,
    LocationGettableProtocol,
    LocationObservableProtocol,
    LocationSettableProtocol,
)


__all__ = [  # noqa: RUF022
    # =========================================================================
    # GENERAL: ARITHMETIC
    # =========================================================================
    "AddableBase",
    "AddableProtocol",
    "SubtractableBase",
    "SubtractableProtocol",
    "NegatableBase",
    "NegatableProtocol",
    "MultiplyableBase",
    "MultiplyableProtocol",
    "DivisibleBase",
    "DivisibleProtocol",
    "ModuloableBase",
    "ModuloableProtocol",
    "PowerableBase",
    "PowerableProtocol",
    "AdditiveBase",
    "AdditiveProtocol",
    "MultiplicativeBase",
    "MultiplicativeProtocol",
    "NumericBase",
    "NumericProtocol",
    # =========================================================================
    # GENERAL: COMPARISON
    # =========================================================================
    "OrderableBase",
    "OrderableProtocol",
    "EqualableBase",
    "EqualableProtocol",
    "ComparableBase",
    "ComparableProtocol",
    # =========================================================================
    # GENERAL: LOGICAL
    # =========================================================================
    "AndableBase",
    "AndableProtocol",
    "OrableBase",
    "OrableProtocol",
    "NotableBase",
    "NotableProtocol",
    "LogicalBase",
    "LogicalProtocol",
    # =========================================================================
    # GENERAL: BITWISE
    # =========================================================================
    "BitwiseAndableBase",
    "BitwiseAndableProtocol",
    "BitwiseOrableBase",
    "BitwiseOrableProtocol",
    "BitwiseXorableBase",
    "BitwiseXorableProtocol",
    "BitwiseInvertableBase",
    "BitwiseInvertableProtocol",
    "ShiftableBase",
    "ShiftableProtocol",
    "BitwiseBase",
    "BitwiseProtocol",
    # =========================================================================
    # COLLECTION: ATOMS
    # =========================================================================
    "ContainableBase",
    "ContainableProtocol",
    "LengthableBase",
    "LengthableProtocol",
    "IndexableBase",
    "IndexableProtocol",
    "SliceableBase",
    "SliceableProtocol",
    # =========================================================================
    # COLLECTION: ITERABLE
    # =========================================================================
    "IterableBase",
    "IterableProtocol",
    # =========================================================================
    # COLLECTION: COLLECTION
    # =========================================================================
    "CollectionBase",
    "CollectionProtocol",
    # =========================================================================
    # COLLECTION: SEQUENCE (+ Mutable)
    # =========================================================================
    "SequenceBase",
    "SequenceProtocol",
    "MutableSequenceBase",
    "MutableSequenceProtocol",
    # =========================================================================
    # COLLECTION: MAPPING (+ Mutable)
    # =========================================================================
    "MappingBase",
    "MappingProtocol",
    "MutableMappingBase",
    "MutableMappingProtocol",
    # =========================================================================
    # COLLECTION: SET (+ Mutable)
    # =========================================================================
    "SetLikeBase",
    "SetLikeProtocol",
    "MutableSetBase",
    "MutableSetProtocol",
    # =========================================================================
    # COLLECTION: CLEARABLE
    # =========================================================================
    "ClearableBase",
    "ClearableProtocol",
    # =========================================================================
    # LOCATION CAPABILITIES (protocol-only)
    # =========================================================================
    "LocationGettableProtocol",
    "LocationSettableProtocol",
    "LocationExistableProtocol",
    "LocationDeletableProtocol",
    "LocationObservableProtocol",
]
