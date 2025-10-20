"""Redwood ABC (Abstract Base Classes) module.

This module defines the abstract base classes (ABCs).
These ABCs provide a common types, interfaces and set of behaviors for various components within the framework.
"""

from __future__ import annotations

from .collections import (
    MappingProtocol,
    MutableMappingProtocol,
)
from .special import (
    EMPTY,
    NAN,
    Empty,
    NaN,
    SpecialValue,
    is_empty,
    is_nan,
    is_special,
    propagate_special,
)
from .types import (
    CallbackFn,
    CompositeValue,
    IterableValues,
    KeyComponent,
    PrimitiveValue,
    TupleKey,
    Value,
)


__all__ = [  # noqa: RUF022
    # Base types
    "CallbackFn",
    "CompositeValue",
    "KeyComponent",
    "PrimitiveValue",
    "TupleKey",
    "Value",
    "IterableValues",
    # Special sentinels
    "EMPTY",
    "NAN",
    "Empty",
    "NaN",
    "SpecialValue",
    "is_empty",
    "is_nan",
    "is_special",
    "propagate_special",
    # Collections
    "MappingProtocol",
    "MutableMappingProtocol",
]
