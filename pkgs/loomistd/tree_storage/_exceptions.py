from __future__ import annotations

__all__ = [
    "TreeError",
    "ObjectTypeError",
    "ObjectKeyError",
    "ObjectIndexError",
]


class TreeError(Exception):
    """Base error for tree operations."""

    pass


class ObjectTypeError(TreeError):
    """Error raised when an operation is performed on the wrong type of tree object."""

    pass


class ObjectKeyError(TreeError):
    """Error raised when a key or path doesn't exist in a tree object."""

    pass


class ObjectIndexError(TreeError):
    """Error raised when an index is out of range in a tree list."""

    pass
