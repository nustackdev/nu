"""EveryShape types module.

This module defines the primitive types and special values.
"""

from __future__ import annotations

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


__all__ = [
    "EMPTY",
    "INVALID",
    "Empty",
    "Invalid",
    "Sentinel",
    "is_empty",
    "is_invalid",
    "is_sentinel",
    "propagate_special",
]
