"""Type hierarchy for everybase.

ObjectType → TypeBase → concrete types (primitives, collections, special).

Organized into:
- object.py: ObjectType (universal base — sentinel checks)
- base.py: TypeBase (everybase kernel identity)
- primitives/: int, float, bool, str, bytes, none
- collections/: list, dict, set, frozenset, tuple
- special/: any, sentinel, empty, invalid
"""

from .base import TypeBase
from .collections import DictType, FrozenSetType, ListType, SetType, TupleType
from .object import ObjectType
from .primitives import BoolType, BytesType, FloatType, IntType, NoneType, StrType
from .special import AnyType, EmptyType, InvalidType, SentinelType


__all__ = [  # noqa: RUF022
    "ObjectType",
    "TypeBase",
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
    "SentinelType",
    "EmptyType",
    "InvalidType",
]
