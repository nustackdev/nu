"""Path navigation system.

Minimal, practical navigation that works through Views using the Nestable protocol.
Views handle their own path translation (e.g., ListView negative indexing).

This module provides:
- Types: ViewPath, ValuePath, segments
- Path helpers: Build, split, join paths (~6 functions)
- Navigation: Traverse through Views (~4 functions)

That's it. Everything else is just tuple operations Python already gives you.
"""

from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from everykv.view import View

    from .path_def import (
        Path,
        PathAddress,
        PathSegment,
        PathToValue,
        PathToView,
        PathValueSegment,
        PathViewSegment,
    )


__all__ = [  # noqa: RUF022
    # Path helpers
    "build_view_path",
    "build_value_path",
    "split_value_path",
    "parent_view_path",
    "last_segment",
    "split_path",
    # Navigation
    "open_child_view",
    "navigate_view",
    "navigate_value",
    "open_parent_view",
]


# =============================================================================
# PATH HELPERS
# =============================================================================


def build_view_path(*segments: PathViewSegment) -> PathToView:
    """Build ViewPath from segments.

    Example:
        >>> path = build_view_path(
        ...     ("users", DictView),
        ...     ("alice", DictView),
        ... )
    """
    return segments


def build_value_path(*segments: *tuple[PathViewSegment, ...], v: PathValueSegment) -> PathToValue:
    """Build ValuePath from segments.

    Example:
        >>> path = build_value_path(
        ...     ("users", DictView),
        ...     ("alice", DictView),
        ...     v=("name", str),
        ... )
    """
    return (*segments, v)


def split_value_path(path: PathToValue) -> tuple[PathToView, PathValueSegment]:
    """Split ValuePath into parent ViewPath and final value segment.

    Args:
        path: ValuePath to split

    Returns:
        (parent ViewPath, value segment)

    Example:
        >>> path = (("users", DictView), ("alice", DictView), ("name", str))
        >>> parent, (address, type) = split_value_path(path)
        >>> # parent = (("users", DictView), ("alice", DictView))
        >>> # address = "name", type = str
    """
    return path[:-1], path[-1]


def split_path(path: Path, index: int) -> tuple[Path, Path]:
    """Split Path (both value and view) into parent Path and final value segment.

    Args:
        path: Path to split
        index: Position to split

    Returns:
        (parent Path, value segment)

    Example:
        >>> path = (("users", DictView), ("alice", DictView), ("name", str))
        >>> parent, (address, type) = split_value_path(path)
        >>> # parent = (("users", DictView), ("alice", DictView))
        >>> # address = "name", type = str
    """
    return path[:index], path[index:]  # type: ignore


def parent_view_path(path: Path) -> PathToView:
    """Get parent ViewPath by removing last segment.

    Example:
        >>> path = (("users", DictView), ("alice", DictView))
        >>> parent = parent_view_path(path)
        >>> # parent = (("users", DictView),)
    """
    return path[:-1]


def last_segment(path: Path) -> PathSegment:
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
    address: PathAddress,
    child_view_type: type[View],
) -> View:
    """Navigate from parent to child View.

    Uses Nestable protocol - parent View handles path translation.

    Args:
        parent_view: Parent view (must be Nestable)
        address: Address in parent's domain (e.g., -1 for ListView)
        child_view_type: Expected child View type

    Returns:
        Child view

    Example:
        >>> users = get_root_view(DictView, tx, registry)
        >>> alice = open_child_view(users, "alice", DictView)
        >>> tags = open_child_view(alice, "tags", ListView)
        >>> last = open_child_view(tags, -1, DictView)  # Negative index!
    """
    from everykv.typing.view import is_nestable

    if not is_nestable(parent_view):
        raise TypeError(
            f"{type(parent_view).__name__} is not Nestable. Cannot navigate to children."
        )

    return parent_view.open_child(address, child_view_type)


def navigate_view(
    start_view: View,
    path: PathToView,
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

    for address, expected_type in path:
        current_view = open_child_view(current_view, address, expected_type)

    return current_view


def navigate_value(
    start_view: View,
    path: PathToValue,
) -> tuple[View, PathAddress]:
    """Navigate ValuePath and return (parent View, value address).

    This returns the parent View and address so you can do view.get(address) or
    view[address] yourself. Useful when you need the View for other operations.

    Args:
        start_view: Starting view
        path: PathToValue to navigate

    Returns:
        (parent View, value address) - call parent._get_child_value(address)

    Example:
        >>> root = get_root_view(DictView, tx, registry)
        >>> path = (("users", DictView), ("alice", DictView), ("name", str))
        >>> parent, address = navigate_value(root, path)
        >>> name = parent._get_child_value(address)  # or parent[address]
        >>> # name = "Alice"

        >>> # With negative indexing
        >>> path = (("users", DictView), ("alice", DictView), ("tags", ListView), (-1, str))
        >>> parent, address = navigate_value(root, path)
        >>> # parent is ListView, address is -1
        >>> # parent handles -1 → actual last index
    """
    if len(path) == 0:
        raise ValueError("Cannot navigate empty ValuePath")

    parent_path, (value_address, _) = split_value_path(path)

    if len(parent_path) > 0:
        parent_view = navigate_view(start_view, parent_path)
    else:
        parent_view = start_view

    return parent_view, value_address


def open_parent_view(child_view: View) -> View:
    """Navigate to parent view.

    Example:
        >>> alice = navigate_view(root, (("users", DictView), ("alice", DictView)))
        >>> users = open_parent_view(alice)
    """
    return child_view.open_parent()
