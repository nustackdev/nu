"""Abstract ref bases combining traits.

These are abstract bases that combine traits for common value types.
Concrete implementations (like IntValue in py/) inherit from these
and add substrate-specific get() implementations.

Example:
    IntType = Numeric + Comparable + Logical + Bitwise + base execution
    IntValue(IntType) = IntType + Python memory get()
    KVIntRef(IntType) = IntType + KV storage get()
"""

from .base import TypeBase
from .type_any import AnyType
from .type_bool import BoolType
from .type_bytes import BytesType
from .type_dict import DictType
from .type_float import FloatType
from .type_int import IntType
from .type_list import ListType
from .type_none import NoneType
from .type_sentinel import EmptyType, InvalidType, SentinelType
from .type_set import FrozenSetType, SetType
from .type_str import StrType
from .type_tuple import TupleType


__all__ = [  # noqa: RUF022
    "TypeBase",
    # Primitives
    "BoolType",
    "IntType",
    "FloatType",
    "StrType",
    "BytesType",
    # Collections
    "ListType",
    "DictType",
    "SetType",
    "FrozenSetType",
    "TupleType",
    # Special
    "AnyType",
    "NoneType",
    "SentinelType",
    "EmptyType",
    "InvalidType",
]
