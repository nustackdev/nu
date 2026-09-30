"""The refs that address KV storage: one slot in a shape, one place on disk.

A slot's ref class decides how its value is laid out, and that is the one
choice worth thinking about. A leaf holds one value read and written whole,
with its value form mixed in. A container gives each element an address of its
own, and the value it declares types every descent and every read. A blob
container holds a whole collection as one leaf value.

The substrate bases (``ItemRef``, ``PrimitiveRef``, ``ViewRef``, ``Facet``)
are here for fabric and library authors; a subscript never hands one back.
"""

from .base import Facet, PrimitiveRef, ViewRef
from .containers import DictRef, ListRef, SetRef, ShapeRef
from .items import BoolRef, BytesRef, FloatRef, IntRef, ItemRef, ObjectRef, StrRef
from .kh57 import Kh57Ref
from .primitives import (
    PrimitiveDictRef,
    PrimitiveFrozenSetRef,
    PrimitiveListRef,
    PrimitiveSetRef,
    PrimitiveTupleRef,
)
from .prog import ProgramRef
from .std import (
    BasisPointRef,
    ComplexRef,
    DateRef,
    DatetimeRef,
    DecimalRef,
    FractionRef,
    PathRef,
    PercentageRef,
    TimedeltaRef,
    TimeRef,
    TimezoneRef,
    UUIDRef,
)


__all__ = [
    "BasisPointRef",
    "BoolRef",
    "BytesRef",
    "ComplexRef",
    "DateRef",
    "DatetimeRef",
    "DecimalRef",
    "DictRef",
    "Facet",
    "FloatRef",
    "FractionRef",
    "IntRef",
    "ItemRef",
    "Kh57Ref",
    "ListRef",
    "ObjectRef",
    "PathRef",
    "PercentageRef",
    "PrimitiveDictRef",
    "PrimitiveFrozenSetRef",
    "PrimitiveListRef",
    "PrimitiveRef",
    "PrimitiveSetRef",
    "PrimitiveTupleRef",
    "ProgramRef",
    "SetRef",
    "ShapeRef",
    "StrRef",
    "TimeRef",
    "TimedeltaRef",
    "TimezoneRef",
    "UUIDRef",
    "ViewRef",
]
