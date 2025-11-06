"""Tree layer exception hierarchy.

This module defines all tree-specific exceptions with a clear hierarchy
that reflects the different error categories in tree operations.
"""

from __future__ import annotations


__all__ = [
    "InvalidDepthError",
    "ParentMalformedError",
    "ParentNotFoundError",
    "PathCollisionError",
    "PathExistsError",
    "PathNotFoundError",
    "PathTypeError",
    "TreeError",
]


class TreeError(Exception):
    """Base exception for all tree layer errors.

    All tree-specific exceptions inherit from this base class,
    allowing for broad exception handling when needed.
    """


class PathNotFoundError(TreeError):
    """Path does not exist in storage.

    Raised when attempting to access or validate a path that
    doesn't exist in the underlying storage.
    """


class PathExistsError(TreeError):
    """Path already exists in storage.

    Raised when attempting to create a node at a path that
    already contains data, typically with incompatible type.
    """


class InvalidPathError(TreeError):
    """Invalid path.

    Raised when:
    - Path is empty tuple
    - Path root segment is neither of / and /m
    """


class PathTypeError(TreeError):
    """Type mismatch or malformed data at path.

    Raised when:
    - Expected type doesn't match actual type
    - Data at path is corrupted or malformed
    - Type information cannot be parsed
    """


class PathCollisionError(PathTypeError):
    """Primitive value collides with container path.

    Raised when a primitive value exists at a path where a
    container is expected, or vice versa. This is a specific
    type of PathTypeError.
    """


class ParentNotFoundError(PathNotFoundError):
    """Parent path is missing from storage.

    Raised when parent containers required for an operation
    don't exist. This is a specific case of PathNotFoundError
    focused on parent chain issues.
    """


class ParentMalformedError(PathTypeError):
    """Parent has corrupted or invalid data.

    Raised when parent containers exist but have malformed
    type markers or corrupted data. This is a specific case
    of PathTypeError focused on parent chain issues.
    """


class InvalidDepthError(TreeError):
    """Invalid depth parameter provided.

    Raised when a depth parameter is invalid (e.g., negative
    when positive required, exceeds maximum allowed depth).
    """
