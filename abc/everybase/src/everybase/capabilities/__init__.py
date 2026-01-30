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
    Collection:  CollectionBase/Protocol  = Containable + Lengthable + Iterable
    Sequence:    SequenceBase/Protocol    = Collection + Sliceable + first/last/sorted/...
    Mapping:     MappingBase/Protocol     = Collection + keys_/values_/items_/get_
    SetLike:     SetLikeBase/Protocol     = Collection + union/intersection/difference/...
"""

from .col_atoms_base import (
    ContainableBase,
    IndexableBase,
    LengthableBase,
    SliceableBase,
)
from .col_atoms_protocol import (
    ContainableProtocol,
    IndexableProtocol,
    LengthableProtocol,
    SliceableProtocol,
)
from .col_collection_base import (
    CollectionBase,
)
from .col_collection_protocol import (
    CollectionProtocol,
)
from .col_iterable_base import (
    IterableBase,
)
from .col_iterable_protocol import (
    IterableProtocol,
)
from .col_mapping_base import (
    MappingBase,
)
from .col_mapping_protocol import (
    MappingProtocol,
)
from .col_sequence_base import (
    SequenceBase,
)
from .col_sequence_protocol import (
    SequenceProtocol,
)
from .col_set_base import (
    SetLikeBase,
)
from .col_set_protocol import (
    SetLikeProtocol,
)
from .gen_arithmetic_base import (
    AddableBase,
    AdditiveBase,
    DivisibleBase,
    ModuloableBase,
    MultiplicativeBase,
    MultiplyableBase,
    NegatableBase,
    NumericBase,
    PowerableBase,
    SubtractableBase,
)
from .gen_arithmetic_protocol import (
    AddableProtocol,
    AdditiveProtocol,
    DivisibleProtocol,
    ModuloableProtocol,
    MultiplicativeProtocol,
    MultiplyableProtocol,
    NegatableProtocol,
    NumericProtocol,
    PowerableProtocol,
    SubtractableProtocol,
)
from .gen_bitwise_base import (
    BitwiseAndableBase,
    BitwiseBase,
    BitwiseInvertableBase,
    BitwiseOrableBase,
    BitwiseXorableBase,
    ShiftableBase,
)
from .gen_bitwise_protocol import (
    BitwiseAndableProtocol,
    BitwiseInvertableProtocol,
    BitwiseOrableProtocol,
    BitwiseProtocol,
    BitwiseXorableProtocol,
    ShiftableProtocol,
)
from .gen_comparison_base import (
    ComparableBase,
    EqualableBase,
    OrderableBase,
)
from .gen_comparison_protocol import (
    ComparableProtocol,
    EqualableProtocol,
    OrderableProtocol,
)
from .gen_logical_base import (
    AndableBase,
    LogicalBase,
    NotableBase,
    OrableBase,
)
from .gen_logical_protocol import (
    AndableProtocol,
    LogicalProtocol,
    NotableProtocol,
    OrableProtocol,
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
    # COLLECTION: SEQUENCE
    # =========================================================================
    "SequenceBase",
    "SequenceProtocol",
    # =========================================================================
    # COLLECTION: MAPPING
    # =========================================================================
    "MappingBase",
    "MappingProtocol",
    # =========================================================================
    # COLLECTION: SET
    # =========================================================================
    "SetLikeBase",
    "SetLikeProtocol",
]
