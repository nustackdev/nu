"""Type definitions."""

from collections.abc import Callable
from typing import Any, TypeVar


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
PrimitiveValue = type(None) | bytes | bool | int | float | complex | str

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
CompositeValue = (
    list[Any]
    | set[Any]
    | dict[Any, Any]
    | frozenset["PrimitiveValue | CompositeValue"]
    | tuple["PrimitiveValue | CompositeValue", ...]
)

# A union of all supported value types
Value = PrimitiveValue | CompositeValue

# ---------------------------------------------------------
# Key types
# ---------------------------------------------------------
# Keys are tuples of strings and integers, used for identifying
# entries in storage systems. Keys are used in codec encoding/decoding,
# storage, and observer notifications.
# ---------------------------------------------------------

# Key type - a tuple of strings and integers
KeyComponent = str | int
Key = tuple[KeyComponent, ...]


# ---------------------------------------------------------
# Reactive types
# ---------------------------------------------------------
# Reactive programming constructs like observers and callbacks
# use keys and paths to identify data points of interest.
# ---------------------------------------------------------

CallbackFn = Callable[[Key], None]


# =========================================================
# Codec-related types
# =========================================================
EncodedKey = Any  # Encoded key type (e.g. bytes, str)
EncodedValue = Any  # Encoded value type (e.g. bytes, str)

# Type variables for generics
EncodedKeyT = TypeVar("EncodedKeyT", bound=EncodedKey)
EncodedValueT = TypeVar("EncodedValueT", bound=EncodedValue)
