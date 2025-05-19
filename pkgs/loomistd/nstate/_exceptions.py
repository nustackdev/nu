# _exceptions.py

"""
Hierarchical exception system for the state management library.

This module defines a comprehensive set of exceptions that follow a clear hierarchy,
making error handling and debugging more intuitive.
"""


class StateError(Exception):
    """Base exception class for all state-related errors."""

    pass


# Path-related exceptions
class PathError(StateError):
    """Base exception class for errors related to path operations."""

    pass


class PathNotFoundError(PathError):
    """Raised when attempting to access a path that does not exist."""

    pass


class PathExistsError(PathError):
    """Raised when attempting to create a path that already exists."""

    pass


class PathTypeError(PathError):
    """Raised when a path exists but is of an incompatible type for the operation."""

    pass


class InvalidPathError(PathError):
    """Raised when a path specification is invalid."""

    pass


# Container-related exceptions
class ContainerError(StateError):
    """Base exception class for errors related to container operations."""

    pass


class ContainerProtocolError(ContainerError):
    """Raised when attempting an operation unsupported by a container's protocols."""

    pass


class ContainerTypeError(ContainerError):
    """Raised when a container is of an incompatible type for the operation."""

    pass


# View-related exceptions
class ViewError(StateError):
    """Base exception class for errors related to view operations."""

    pass


class IncompatibleViewError(ViewError):
    """Raised when attempting to use a view incompatible with a container's protocols."""

    pass


# Operation-related exceptions
class OperationError(StateError):
    """Base exception class for errors related to state operations."""

    pass


class ReadOnlyError(OperationError):
    """Raised when attempting to modify a read-only structure."""

    pass


class TypeConversionError(OperationError):
    """Raised when a type conversion fails."""

    pass


class SerializationError(OperationError):
    """Raised when serialization or deserialization fails."""

    pass
