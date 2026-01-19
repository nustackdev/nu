"""Container layer exception hierarchy.

This module defines all container-specific exceptions with a clear hierarchy
that reflects the different error categories in container operations.
"""

from __future__ import annotations

from everykv._exception import EveryShapeError


__all__ = [
    "ContainerCollisionError",
    "ContainerError",
    "ContainerExistsError",
    "ContainerInvalidDepthError",
    "ContainerInvalidSiteError",
    "ContainerNotFoundError",
    "ContainerParentMalformedError",
    "ContainerParentNotFoundError",
    "ContainerTypeError",
]


class ContainerError(EveryShapeError):
    """Base exception for all container layer errors.

    All container-specific exceptions inherit from this base class,
    allowing for broad exception handling when needed.
    """


class ContainerNotFoundError(ContainerError):
    """Site does not exist in storage.

    Raised when attempting to access or validate a site that
    doesn't exist in the underlying storage.
    """


class ContainerExistsError(ContainerError):
    """Site already exists in storage.

    Raised when attempting to create a node at a site that
    already contains data, typically with incompatible type.
    """


class ContainerInvalidSiteError(ContainerError):
    """Invalid site.

    Raised when:
    - Site is empty tuple
    - Site root segment is neither of / and /m
    """


class ContainerTypeError(ContainerError):
    """Type mismatch or malformed data at site.

    Raised when:
    - Expected type doesn't match actual type
    - Data at site is corrupted or malformed
    - Type information cannot be parsed
    """


class ContainerCollisionError(ContainerTypeError):
    """Primitive value collides with container site.

    Raised when a primitive value exists at a site where a
    container is expected, or vice versa. This is a specific
    type of ContainerTypeError.
    """


class ContainerParentNotFoundError(ContainerNotFoundError):
    """Parent site is missing from storage.

    Raised when parent containers required for an operation
    don't exist. This is a specific case of ContainerNotFoundError
    focused on parent chain issues.
    """


class ContainerParentMalformedError(ContainerTypeError):
    """Parent has corrupted or invalid data.

    Raised when parent containers exist but have malformed
    type markers or corrupted data. This is a specific case
    of ContainerTypeError focused on parent chain issues.
    """


class ContainerInvalidDepthError(ContainerError):
    """Invalid depth parameter provided.

    Raised when a depth parameter is invalid (e.g., negative
    when positive required, exceeds maximum allowed depth).
    """
