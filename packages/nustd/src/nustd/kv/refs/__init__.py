"""The refs that address KV storage: one slot in a shape, one place on disk.

Two substrates underneath, and everything else is a specialisation of one of
them. ``ViewRef`` reads as a live container view, so collection ops run
against storage; ``PrimitiveRef`` subscripts its parent, so a leaf reads as
its value.

Which ref a slot is declared with decides how the value is laid out, and that
is the one choice worth thinking about:

- Leaves: ``ItemRef`` untyped, ``IntRef`` / ``StrRef`` / ``FloatRef`` /
  ``BoolRef`` / ``BytesRef`` typed, each with its Form's operators.
- Std-library leaves: ``DecimalRef``, ``FractionRef``, ``ComplexRef``,
  ``BasisPointRef``, ``PercentageRef``, ``DateRef``, ``DatetimeRef``,
  ``TimeRef``, ``TimedeltaRef``, ``TimezoneRef``, ``PathRef``, ``UUIDRef``.
  Each stores a form the substrate can hold and lifts it back on read.
- Decomposed containers: ``ListRef``, ``DictRef``, ``SetRef``, ``ShapeRef``,
  ``ShapesListRef``, ``ShapesDictRef``. Elements get their own addresses, so
  they can be read, written and watched one at a time.
- Whole-blob containers: ``PrimitiveListRef``, ``PrimitiveDictRef``,
  ``PrimitiveTupleRef``, ``PrimitiveSetRef``, ``PrimitiveFrozenSetRef``. One
  opaque value, heterogeneous contents, no per-element addresses.
- Sampled maps: ``Kh57Ref`` and ``Kh57ShapesRef``, int-keyed and laid out so
  a sample of a key range costs the same at any scale.
- ``ProgramRef``: Nu source stored in a leaf, runnable from the slot.
"""

from .base import Facet, PrimitiveRef, ViewRef
from .dict import DictRef
from .dictshape import ShapesDictRef
from .items import BoolRef, BytesRef, FloatRef, IntRef, ItemRef, StrRef
from .kh57 import Kh57Ref
from .kh57shape import Kh57ShapesRef
from .list import ListRef
from .listshape import ShapesListRef
from .primitives import (
    PrimitiveDictRef,
    PrimitiveFrozenSetRef,
    PrimitiveListRef,
    PrimitiveSetRef,
    PrimitiveTupleRef,
)
from .prog import ProgramRef
from .set import SetRef
from .shape import ShapeRef
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
    "Kh57ShapesRef",
    "ListRef",
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
    "ShapesDictRef",
    "ShapesListRef",
    "StrRef",
    "TimeRef",
    "TimedeltaRef",
    "TimezoneRef",
    "UUIDRef",
    "ViewRef",
]
