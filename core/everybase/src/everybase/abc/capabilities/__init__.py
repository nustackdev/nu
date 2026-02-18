"""Capability protocols and bases for refs.

Each capability has a paired Protocol (structural type contract) and Base (mixin implementation).
Protocols declare the public interface; Bases provide morphism-wrapping implementations.

    GENERAL OPERATIONS
    ──────────────────────────
    Arithmetic:  AddableBase/Protocol … NumericBase/Protocol
    Comparison:  OrderableBase/Protocol, EqualableBase/Protocol, ComparableBase/Protocol
    Logical:     AndableBase/Protocol … LogicalBase/Protocol
    Bitwise:     BitwiseAndableBase/Protocol … BitwiseBase/Protocol

    COLLECTION OPERATIONS
    ─────────────────────────────
    Atoms:       ContainableBase/Protocol, LengthableBase/Protocol, IndexableBase/Protocol, SliceableBase/Protocol
"""

from .arithmetic import (
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
from .bitwise import (
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
from .collection import (
    ContainableBase,
    ContainableProtocol,
    IndexableBase,
    IndexableProtocol,
    LengthableBase,
    LengthableProtocol,
    SliceableBase,
    SliceableProtocol,
)
from .comparison import (
    ComparableBase,
    ComparableProtocol,
    EqualableBase,
    EqualableProtocol,
    OrderableBase,
    OrderableProtocol,
)
from .logical import (
    AndableBase,
    AndableProtocol,
    LogicalBase,
    LogicalProtocol,
    NotableBase,
    NotableProtocol,
    OrableBase,
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
]
