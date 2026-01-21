"""Capability traits for refs.

Traits define what operations a ref supports. They are mixins that provide
operator overloads and methods that return morphism-wrapped results.

Hierarchy:
    ARITHMETIC
    ──────────
    Addable           →  __add__, __radd__
    Subtractable      →  __sub__, __rsub__
    Negatable         →  __neg__, __pos__, __abs__
    Multiplyable      →  __mul__, __rmul__
    Divisible         →  __truediv__, __floordiv__
    Powerable         →  __pow__, __rpow__
    Moduloable        →  __mod__, __rmod__

    Additive = Addable + Subtractable + Negatable
    Multiplicative = Multiplyable + Divisible + Moduloable + Powerable
    Numeric = Additive + Multiplicative


    COMPARISON
    ──────────
    Orderable         →  __lt__, __gt__, __le__, __ge__
    Equalable         →  eq(), ne(), is_()

    Comparable = Orderable + Equalable


    LOGICAL
    ───────
    Andable           →  and_()
    Orable            →  or_()
    Notable           →  not_(), bool_()

    Logical = Andable + Orable + Notable


    BITWISE
    ───────
    BitwiseAndable    →  bitand()
    BitwiseOrable     →  bitor()
    BitwiseXorable    →  __xor__, __rxor__
    BitwiseInvertable →  bitnot()
    Shiftable         →  __lshift__, __rshift__

    Bitwise = BitwiseAndable + BitwiseOrable + BitwiseXorable + BitwiseInvertable + Shiftable


    COLLECTION
    ──────────
    Lengthable        →  len_()
    Indexable         →  __getitem__
    Sliceable         →  slice_()
    Containable       →  contains()
    Iterable          →  map_(), filter_(), reduce_()

    Sequence = Lengthable + Sliceable + Containable + Iterable
    Mapping = Lengthable + Containable + keys/values/items
    SetLike = Lengthable + Containable + set operations
"""

from .arithmetic import (
    Addable,
    Additive,
    Divisible,
    Moduloable,
    Multiplicative,
    Multiplyable,
    Negatable,
    Numeric,
    Powerable,
    Subtractable,
)
from .bitwise import (
    Bitwise,
    BitwiseAndable,
    BitwiseInvertable,
    BitwiseOrable,
    BitwiseXorable,
    Shiftable,
)
from .collection import (
    Containable,
    Indexable,
    Iterable,
    Lengthable,
    Mapping,
    Sequence,
    SetLike,
    Sliceable,
)
from .comparison import (
    Comparable,
    Equalable,
    Orderable,
)
from .logical import (
    Andable,
    Logical,
    Notable,
    Orable,
)


__all__ = [  # noqa: RUF022
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
]
