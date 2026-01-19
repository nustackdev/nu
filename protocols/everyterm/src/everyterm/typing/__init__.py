"""EveryShape types module.

This module defines the primitive types and special values.
"""

from __future__ import annotations

from .not_set import NOT_SET, NotSet, is_notset
from .sentinel import (
    EMPTY,
    INVALID,
    Empty,
    Invalid,
    Sentinel,
    is_empty,
    is_invalid,
    is_sentinel,
    propagate_special,
)


__all__ = [  # noqa: RUF022
    # Special sentinels
    "EMPTY",
    "INVALID",
    "Empty",
    "Invalid",
    "Sentinel",
    "is_empty",
    "is_invalid",
    "is_sentinel",
    "propagate_special",
    # Not set
    "NotSet",
    "NOT_SET",
    "is_notset",
]
