"""EveryShape types module.

This module defines the primitive types and special values.
"""

from __future__ import annotations

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
    Empty,
    NaN,
    SpecialValue,
    is_empty,
    is_nan,
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
    "Empty",
    "NaN",
    "SpecialValue",
    "is_empty",
    "is_nan",
    "is_special",
    "propagate_special",
]
