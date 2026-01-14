"""EveryShape types module.

This module defines the primitive types and special values.
"""

from __future__ import annotations

from .not_set import NOT_SET, NotSet, is_notset
from .sentinel import (
    EMPTY,
    NAN,
    Empty,
    NaN,
    Sentinel,
    is_empty,
    is_nan,
    is_special,
    propagate_special,
)
from .storage import (
    CompositeValue,
    PrimitiveValue,
    Value,
)


__all__ = [  # noqa: RUF022
    # Storage types
    "CompositeValue",
    "PrimitiveValue",
    "Value",
    # Special sentinels
    "EMPTY",
    "NAN",
    "Empty",
    "NaN",
    "Sentinel",
    "is_empty",
    "is_nan",
    "is_special",
    "propagate_special",
    # Not set
    "NotSet",
    "NOT_SET",
    "is_notset",
]
