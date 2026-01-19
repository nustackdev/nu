"""Unified typed expression.

RValue                  - evaluable expression (has children)
├── Type                - typed value (literal or computed, unified)
│   ├── IntType, FloatType, StrType, BoolType, BytesType
│   ├── NilType, ListType, DictType, SetType, TupleType
│   ├── AnyType         - dynamic/unknown type
│   └── SentinelType    - special values (EmptyType, InvalidType)
"""

from __future__ import annotations

from .type import Type


__all__ = [
    "Type",
]
