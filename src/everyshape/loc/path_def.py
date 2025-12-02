"""Core definitions for Path location.

This module defines the fundamental types used throughout the Path navigation system.

Paths are primarily used in the View layer.
"""

from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from everyshape.types import Value
    from everyshape.view import View

__all__ = [
    "Path",
    "PathAddress",
    "PathSegment",
    "PathSegmentType",
    "PathToValue",
    "PathToView",
    "PathValueSegment",
    "PathViewSegment",
]


# =============================================================================
# CORE TYPES
# =============================================================================

type PathAddress = object
"""First component in a path segment (address, type).

This can be ANY object that the View understands:
- String keys for DictView: "users", "alice"
- Integer indexes for ListView: 0, 1, -1, -2 (including negative!)
- Custom objects for custom Views: hash values, symbolic names, timestamps

The View's open_view() method translates these to storage keys.

Examples:
    "alice"              # DictView key
    -1                   # ListView index (last element!)
    "LATEST"             # Custom TimeSeriesView loc
    hash("user:alice")   # Custom HashMapView key
"""

type PathSegmentType = Value | type[View]
"""Second component in a path segment (address, type).

Can be either a View type or a Value (str, int, dict, etc):
- View's are used for View navigation
- Valus's indicate type of a final primitive object (leaf object)
"""

type PathViewSegment = tuple[PathAddress, type[View]]
"""Single navigation step to a View (container).

A ViewSegment specifies:
1. The address to navigate with (in parent View's domain)
2. The expected View type at that location

Examples:
    ("users", DictView)     # Navigate to "users", expect DictView
    ("alice", DictView)     # Navigate to "alice", expect DictView
    (0, ListView)           # Navigate to index 0, expect ListView
    (-1, DictView)          # Navigate to last item, expect DictView
"""


type PathValueSegment = tuple[PathAddress, Value]
"""Single navigation step to a primitive value.

A ValueSegment specifies:
1. The key to navigate with (in parent View's domain)
2. The expected primitive type at that location

The type is for documentation/validation only - it's not a View type.

Examples:
    ("name", str)           # Navigate to "name", expect string
    ("age", int)            # Navigate to "age", expect integer
    (-1, str)               # Navigate to last item, expect string
    ("price", float)        # Navigate to "price", expect float
"""

type PathSegment = tuple[PathAddress, PathSegmentType]
"""A single navigation step in a Path.

Can be both a navigation to a primitive value and to a view.

Constst from address and type: (PathAddress, PathSegmentType).

Examples:
    ("name", str)           # "name" -> PathAddress, str -> PathSegmentType
    ("alice", DictView)     # "alice" -> PathAddress, DictView -> PathSegmentType
"""

type PathToView = tuple[PathViewSegment, ...]
"""Path that ends at a View (container).

All segments in a ViewPath point to View types. Navigating a ViewPath
returns a View instance that can be further navigated or manipulated.

Examples:
    # Empty path (already at target)
    ()

    # Path to users dict
    (("users", DictView),)

    # Path to alice's data dict
    (
        ("users", DictView),
        ("alice", DictView),
    )

    # Path to alice's tags list
    (
        ("users", DictView),
        ("alice", DictView),
        ("tags", ListView),
    )

Usage:
    >>> root = get_root_view(DictView, tx, registry)
    >>> path = (("users", DictView), ("alice", DictView))
    >>> alice_view = navigate_to_view(root, path)
    >>> # alice_view is a DictView instance
"""


type PathToValue = tuple[*tuple[PathViewSegment, ...], PathValueSegment]
"""Path that ends at a primitive value.

A ValuePath consists of:
- Zero or more ViewSegments (navigating through Views)
- One final ValueSegment (pointing to primitive value)

Navigating a ValuePath returns the actual primitive value, not a View.

Examples:
    # Path to alice's name (string)
    (
        ("users", DictView),
        ("alice", DictView),
        ("name", str),
    )

    # Path to last tag (using negative index!)
    (
        ("users", DictView),
        ("alice", DictView),
        ("tags", ListView),
        (-1, str),  # ListView handles -1 → last element
    )

    # Path to bob's age (integer)
    (
        ("users", DictView),
        ("bob", DictView),
        ("age", int),
    )

Usage:
    >>> root = get_root_view(DictView, tx, registry)
    >>> path = (
    ...     ("users", DictView),
    ...     ("alice", DictView),
    ...     ("name", str),
    ... )
    >>> name = navigate_to_value(root, path)
    >>> # name is "Alice" (string value)

Note:
    The final type (str, int, float, etc.) is for documentation and
    validation. The actual value type should match, but it's not enforced
    by the type system at compile time.
"""

type Path = PathToView | PathToValue
"""
A path is a sequence of typed segments leading to a destination.

Views interpret paths, translating domain keys (like -1 for "last item") into storage keys.
Paths understand protocols - DictView paths vs ListView paths behave differently.

Examples:

```python
# Path to users dict
(
    ("users", DictView),
)

# Path to alice's data dict
(
    ("users", DictView),
    ("alice", DictView),
)

# Path to the last item of alice's tags list
(
    ("users", DictView),
    ("alice", DictView),
    ("tags", ListView),
    (-1, str),
)
```
"""
