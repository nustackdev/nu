"""Abstract ref bases combining traits.

These are abstract bases that combine traits for common value types.
Concrete implementations (like IntValue in py/) inherit from these
and add substrate-specific get() implementations.

Example:
    IntType = Numeric + Comparable + Logical + Bitwise + base execution
    IntValue(IntType) = IntType + Python memory get()
    KVIntRef(IntType) = IntType + KV storage get()
"""

from ._base import TypeBase
from .any import AnyType
from .bool import BoolType
from .bytes import BytesType
from .dict import DictType
from .float import FloatType
from .int import IntType
from .list import ListType
from .none import NoneType_
from .sentinel import EmptyType, InvalidType, SentinelType
from .set import FrozenSetType, SetType
from .str import StrType
from .tuple import TupleType


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
    "NoneType_",
    "SentinelType",
    "EmptyType",
    "InvalidType",
]
