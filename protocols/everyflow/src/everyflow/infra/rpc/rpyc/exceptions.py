"""RPyC-related exceptions for error handling.

This module defines the hierarchy of exceptions that can be raised during
RPyC operations. It provides specific exception types for different
failure scenarios:

- RPyCConnectionError: For connection establishment/management failures
- RPyCOperationError: For remote operation failures
- RPyCServerError: For server-side operation failures

The exceptions form a hierarchy with RPyCError as the base for RPyC-specific
errors, allowing for both specific and general error catching as needed.
"""

from __future__ import annotations


__all__ = [
    "RPyCConnectionError",
    "RPyCError",
    "RPyCOperationError",
    "RPyCServerError",
]


class RPyCError(Exception):
    """Base class for RPyC-related exceptions.

    This exception serves as the base for all RPyC-related errors,
    allowing for specific error types to inherit from it. It provides
    a common interface for handling RPyC errors in a consistent manner.
    """

    pass


class RPyCConnectionError(RPyCError):
    """Exception raised when RPyC connection operations fail.

    This exception indicates failures during connection management, which
    can include:
    - Connection establishment failures
    - Network connectivity issues
    - Server unavailability
    - Connection configuration errors
    """

    pass


class RPyCOperationError(RPyCError):
    """Exception raised when RPyC remote operations fail.

    This exception indicates failures during remote operation execution, which
    can include:
    - Remote method call failures
    - Resource resolution failures
    - Serialization/deserialization errors
    - Remote server errors
    """

    pass


class RPyCServerError(RPyCError):
    """Exception raised when RPyC server operations fail.

    This exception indicates failures on the server side, which
    can include:
    - Resource creation failures
    - Server configuration errors
    - Resource registry errors
    - Server lifecycle management errors
    """

    pass
