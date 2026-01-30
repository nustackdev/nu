"""Capability mixins for refs.

Capabilities define what operations a ref supports. They are mixins that provide
operator overloads and methods that return morphism-wrapped results.

Hierarchy:
    ARITHMETIC (op_arithmetic)
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


    COMPARISON (op_comparison)
    ──────────
    Orderable         →  __lt__, __gt__, __le__, __ge__
    Equalable         →  eq(), ne(), is_()

    Comparable = Orderable + Equalable


    LOGICAL (op_logical)
    ───────
    Andable           →  and_()
    Orable            →  or_()
    Notable           →  not_(), bool_()

    Logical = Andable + Orable + Notable


    BITWISE (op_bitwise)
    ───────
    BitwiseAndable    →  bitand()
    BitwiseOrable     →  bitor()
    BitwiseXorable    →  __xor__, __rxor__
    BitwiseInvertable →  bitnot()
    Shiftable         →  __lshift__, __rshift__

    Bitwise = BitwiseAndable + BitwiseOrable + BitwiseXorable + BitwiseInvertable + Shiftable


    COLLECTION ACCESS (col_access)
    ─────────────────
    Lengthable        →  len_()
    Indexable          →  __getitem__
    Sliceable         →  slice_()
    Containable       →  contains()

    COLLECTION ITERABLE (col_iterable)
    ───────────────────
    Iterable          →  map_(), filter_(), reduce_()

    COLLECTION COMBINED (col_sequence, col_mapping, col_set)
    ───────────────────
    Sequence = Lengthable + Sliceable + Containable + Iterable
    Mapping = Lengthable + Containable + keys/values/items
    SetLike = Lengthable + Containable + set operations
"""

from .col_access import (
    Containable,
    Indexable,
    Lengthable,
    Sliceable,
)
from .col_iterable import (
    Iterable,
)
from .col_mapping import (
    Mapping,
)
from .col_sequence import (
    Sequence,
)
from .col_set import (
    SetLike,
)
from .op_arithmetic import (
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
from .op_bitwise import (
    Bitwise,
    BitwiseAndable,
    BitwiseInvertable,
    BitwiseOrable,
    BitwiseXorable,
    Shiftable,
)
from .op_comparison import (
    Comparable,
    Equalable,
    Orderable,
)
from .op_logical import (
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
