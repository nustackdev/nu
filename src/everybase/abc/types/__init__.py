"""Type hierarchy for everybase.

Object → concrete types (primitives, collections, special).

Organized into:
- object.py: Object (universal base — sentinel checks)
- primitives/: int, float, bool, str, bytes, none
- collections/: list, dict, set, frozenset, tuple
- special/: any, sentinel, empty, invalid
"""

from .collections import DictType, FrozenSetType, ListType, SetType, TupleType
from .object import Object
from .primitives import BoolType, BytesType, FloatType, IntType, NoneType, StrType
from .special import AnyType, EmptyType, InvalidType, IteratorType, SentinelType


__all__ = [  # noqa: RUF022
    "Object",
    # Primitives
    "BoolType",
    "IntType",
    "FloatType",
    "StrType",
    "BytesType",
    "NoneType",
    # Collections
    "ListType",
    "DictType",
    "SetType",
    "FrozenSetType",
    "TupleType",
    # Special
    "AnyType",
    "IteratorType",
    "SentinelType",
    "EmptyType",
    "InvalidType",
]
