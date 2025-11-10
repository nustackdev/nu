"""Redwood ABC (Abstract Base Classes) module.

This module defines the abstract base classes (ABCs).
These ABCs provide a common types, interfaces and set of behaviors for various components within the framework.
"""

from __future__ import annotations

from .capabilities import Convertible, Initializable, Nestable
from .common import (
    CallbackFn,
    CompositeValue,
    IterableValues,
    KeyComponent,
    PrimitiveValue,
    TupleKey,
    Value,
    cast_value,
)
from .mapping import (
    MappingProtocol,
    MutableMappingProtocol,
)
from .special import (
    EMPTY,
    NAN,
    NOT_SET,
    Empty,
    NaN,
    NotSet,
    SpecialValue,
    is_empty,
    is_nan,
    is_notset,
    is_special,
    propagate_special,
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
    "cast_value",
    # Special sentinels
    "EMPTY",
    "NAN",
    "NOT_SET",
    "Empty",
    "NaN",
    "NotSet",
    "SpecialValue",
    "is_empty",
    "is_nan",
    "is_notset",
    "is_special",
    "propagate_special",
    # Capabilities
    "Convertible",
    "Initializable",
    "Nestable",
    # Collections
    "MappingProtocol",
    "MutableMappingProtocol",
]
