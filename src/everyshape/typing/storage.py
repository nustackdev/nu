"""Primitve types."""

from __future__ import annotations

from types import NoneType
from typing import Any


__all__ = [
    "CompositeValue",
    "PrimitiveValue",
    "Value",
]

# =========================================================
# Global types used across the package
# =========================================================

# ---------------------------------------------------------
# Value types
# ---------------------------------------------------------
# Values are broadly classified into:
# - Primitive values: None, bytes, bool, int, float, str
# - Composite values: list, set, dict, frozenset, tuple
#   (which can recursively contain primitive or composite values)
#
# Values are types used for codec encoding/decoding, storage.
# ---------------------------------------------------------

# Base primitive values
type PrimitiveValue = NoneType | bytes | bool | int | float | complex | str

# Composite values.
#
# Mutable containers (list, set, dict) use Any due to type invariance:
# - dict[str, str] is not assignable to dict[str, str | int] even though str ⊂ (str | int)
# - This is because mutable containers could be modified through the broader type
# - Using Any avoids combinatorial explosion of type unions
#
# Immutable containers (tuple, frozenset) use precise types:
# - These are covariant, so tuple[str, ...] IS assignable to tuple[str | int, ...]
# - Safe because they can't be modified after creation
type CompositeValue = (
    list[Any]
    | set[Any]
    | dict[Any, Any]
    | frozenset["PrimitiveValue | CompositeValue"]
    | tuple["PrimitiveValue | CompositeValue", ...]
)

# A union of all supported value types
type Value = PrimitiveValue | CompositeValue
