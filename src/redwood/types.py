"""Type definitions."""

from typing import Any


# A component of a key.
StorageKeyComponent = str | int
# A key in the storage, represented as a tuple of components.
StorageKey = tuple[StorageKeyComponent, ...]

# Base primitive values that should be supported by storage.
PrimitiveValue = type(None) | bytes | bool | int | float | str

# Composite values that should be supported by storage.
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
