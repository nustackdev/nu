"""Type definitions for ABC modules."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any


__all__ = [
    "CallbackFn",
    "CompositeValue",
    "KeyComponent",
    "PrimitiveValue",
    "TupleKey",
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
type PrimitiveValue = None | bytes | bool | int | float | complex | str

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

# Iterable of values. Used in type hints for functions that process collections of values.
type IterableValues = Iterable[Value]

# ---------------------------------------------------------
# Key types
# ---------------------------------------------------------
# Keys are tuples of strings and integers, used for identifying
# entries in storage systems. Keys are used in codec encoding/decoding,
# storage, and observer notifications.
# ---------------------------------------------------------

# Key type - a tuple of strings and integers
type KeyComponent = str | int
type TupleKey = tuple[KeyComponent, ...]


# ---------------------------------------------------------
# Reactive types
# ---------------------------------------------------------
# Reactive programming constructs like observers and callbacks
# use keys and paths to identify data points of interest.
# ---------------------------------------------------------

type CallbackFn = Callable[[TupleKey], None]
