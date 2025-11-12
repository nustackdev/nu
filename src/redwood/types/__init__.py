"""Redwood ABC (Abstract Base Classes) module.

This module defines the abstract base classes (ABCs).
These ABCs provide a common types, interfaces and set of behaviors for various components within the framework.
"""

from __future__ import annotations

from .capabilities import (
    Convertible,
    Initializable,
    Nestable,
    is_convertible,
    is_initializable,
    is_nestable,
)
from .mapping import (
    MappingProtocol,
    MutableMappingProtocol,
)
from .primitive import (
    CompositeValue,
    IterableValues,
    PrimitiveValue,
    Value,
    cast_value,
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
    "CompositeValue",
    "PrimitiveValue",
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
    "is_convertible",
    "is_initializable",
    "is_nestable",
    # Collections
    "MappingProtocol",
    "MutableMappingProtocol",
]
