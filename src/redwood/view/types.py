"""Core type definitions for View navigation.

This module defines the fundamental types used throughout the navigation system:
- ViewKey: Keys in View's domain (can be any object)
- ViewSegment: Navigation step to a View (container)
- ValueSegment: Navigation step to a primitive value
- ViewPath: Path ending at a View
- ValuePath: Path ending at a primitive value
"""

from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from redwood.view import View

__all__ = [
    "ValuePath",
    "ValueSegment",
    "ViewKey",
    "ViewPath",
    "ViewSegment",
]


# =============================================================================
# CORE TYPES
# =============================================================================

type ViewKey = object
"""Key in View's domain (not storage domain).

This can be ANY object that the View understands:
- String keys for DictView: "users", "alice"
- Integer indexes for ListView: 0, 1, -1, -2 (including negative!)
- Custom keys for custom Views: hash values, symbolic names, timestamps

The View's open_view() method translates these to storage keys.

Examples:
    "alice"              # DictView key
    -1                   # ListView key (last element!)
    "LATEST"             # Custom TimeSeriesView key
    hash("user:alice")   # Custom HashMapView key
"""


type ViewSegment = tuple[ViewKey, type["View"]]
"""Single navigation step to a View (container).

A ViewSegment specifies:
1. The key to navigate with (in parent View's domain)
2. The expected View type at that location

Examples:
    ("users", DictView)     # Navigate to "users", expect DictView
    ("alice", DictView)     # Navigate to "alice", expect DictView
    (0, ListView)           # Navigate to index 0, expect ListView
    (-1, DictView)          # Navigate to last item, expect DictView
"""


type ValueSegment = tuple[ViewKey, type]
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


type ViewPath = tuple[ViewSegment, ...]
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


type ValuePath = tuple[ViewSegment | ValueSegment, ...]
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
