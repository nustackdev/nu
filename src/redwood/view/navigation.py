"""View navigation system for Layer 3.

Minimal, practical navigation that works through Views using the Nestable protocol.
Views handle their own key translation (e.g., ListView negative indexing).

This module provides:
- Types: ViewPath, ValuePath, segments
- Path helpers: Build, split, join paths (~6 functions)
- Navigation: Traverse through Views (~4 functions)

That's it. Everything else is just tuple operations Python already gives you.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from redwood.abc import is_nestable


if TYPE_CHECKING:
    from redwood.view import View

    from .types import ValuePath, ValueSegment, ViewKey, ViewPath, ViewSegment


__all__ = [  # noqa: RUF022
    # Path helpers
    "build_view_path",
    "build_value_path",
    "split_value_path",
    "parent_view_path",
    "last_segment",
    # Navigation
    "open_child_view",
    "navigate_view",
    "navigate_value",
    "open_parent_view",
]


# =============================================================================
# PATH HELPERS
# =============================================================================


def build_view_path(*segments: ViewSegment) -> ViewPath:
    """Build ViewPath from segments.

    Example:
        >>> path = build_view_path(
        ...     ("users", DictView),
        ...     ("alice", DictView),
        ... )
    """
    return segments


def build_value_path(*segments: ViewSegment | ValueSegment) -> ValuePath:
    """Build ValuePath from segments.

    Example:
        >>> path = build_value_path(
        ...     ("users", DictView),
        ...     ("alice", DictView),
        ...     ("name", str),
        ... )
    """
    return segments


def split_value_path(path: ValuePath) -> tuple[ViewPath, ValueSegment]:
    """Split ValuePath into parent ViewPath and final value segment.

    Args:
        path: ValuePath to split

    Returns:
        (parent ViewPath, value segment)

    Example:
        >>> path = (("users", DictView), ("alice", DictView), ("name", str))
        >>> parent, (key, type) = split_value_path(path)
        >>> # parent = (("users", DictView), ("alice", DictView))
        >>> # key = "name", type = str
    """
    return path[:-1], path[-1]


def parent_view_path(path: ViewPath) -> ViewPath:
    """Get parent ViewPath by removing last segment.

    Example:
        >>> path = (("users", DictView), ("alice", DictView))
        >>> parent = parent_view_path(path)
        >>> # parent = (("users", DictView),)
    """
    return path[:-1]


def last_segment(path: ViewPath | ValuePath) -> ViewSegment | ValueSegment:
    """Get last segment from path.

    Example:
        >>> path = (("users", DictView), ("alice", DictView))
        >>> last_segment(path)
        ("alice", DictView)
    """
    return path[-1]


# =============================================================================
# NAVIGATION
# =============================================================================


def open_child_view(
    parent_view: View,
    key: ViewKey,
    child_view_type: type[View],
) -> View:
    """Navigate from parent to child View.

    Uses Nestable protocol - parent View handles key translation.

    Args:
        parent_view: Parent view (must be Nestable)
        key: Key in parent's domain (e.g., -1 for ListView)
        child_view_type: Expected child View type

    Returns:
        Child view

    Example:
        >>> users = get_root_view(DictView, tx, registry)
        >>> alice = open_child_view(users, "alice", DictView)
        >>> tags = open_child_view(alice, "tags", ListView)
        >>> last = open_child_view(tags, -1, DictView)  # Negative index!
    """
    if not is_nestable(parent_view):
        raise TypeError(
            f"{type(parent_view).__name__} is not Nestable. Cannot navigate to children."
        )

    return parent_view.open_view(key, child_view_type)


def navigate_view(
    start_view: View,
    path: ViewPath,
) -> View:
    """Navigate ViewPath to reach target View.

    Args:
        start_view: Starting view
        path: ViewPath to navigate

    Returns:
        View at end of path

    Example:
        >>> root = get_root_view(DictView, tx, registry)
        >>> path = (("users", DictView), ("alice", DictView))
        >>> alice = navigate_view(root, path)
    """
    current_view = start_view

    for key, expected_type in path:
        current_view = open_child_view(current_view, key, expected_type)

    return current_view


def navigate_value(
    start_view: View,
    path: ValuePath,
) -> tuple[View, ViewKey]:
    """Navigate ValuePath and return (parent View, value key).

    This returns the parent View and key so you can do view.get(key) or
    view[key] yourself. Useful when you need the View for other operations.

    Args:
        start_view: Starting view
        path: ValuePath to navigate

    Returns:
        (parent View, value key) - call parent._get_child_value(key)

    Example:
        >>> root = get_root_view(DictView, tx, registry)
        >>> path = (("users", DictView), ("alice", DictView), ("name", str))
        >>> parent, key = navigate_value(root, path)
        >>> name = parent._get_child_value(key)  # or parent[key]
        >>> # name = "Alice"

        >>> # With negative indexing
        >>> path = (("users", DictView), ("alice", DictView), ("tags", ListView), (-1, str))
        >>> parent, key = navigate_value(root, path)
        >>> # parent is ListView, key is -1
        >>> # parent handles -1 → actual last index
    """
    if len(path) == 0:
        raise ValueError("Cannot navigate empty ValuePath")

    parent_path, (value_key, _) = split_value_path(path)

    if len(parent_path) > 0:
        parent_view = navigate_view(start_view, parent_path)
    else:
        parent_view = start_view

    return parent_view, value_key


def open_parent_view(child_view: View) -> View:
    """Navigate to parent view.

    Example:
        >>> alice = navigate_view(root, (("users", DictView), ("alice", DictView)))
        >>> users = open_parent_view(alice)
    """
    return child_view.open_parent()
