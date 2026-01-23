# everyflowstd/Invisibles/_exceptions.py
"""Invisibles-related exceptions for error handling.

This module defines the hierarchy of exceptions that can be raised during
Invisibles operations. It provides specific exception types for different
failure scenarios:

- InvisiblesConnectionError: For connection establishment/management failures
- InvisiblesOperationError: For remote operation failures
- InvisiblesServerError: For server-side operation failures

The exceptions form a hierarchy with InvisiblesError as the base for Invisibles-specific
errors, allowing for both specific and general error catching as needed.
"""

from __future__ import annotations


__all__ = [
    "InvisiblesConnectionError",
    "InvisiblesError",
    "InvisiblesOperationError",
    "InvisiblesServerError",
]


class InvisiblesError(Exception):
    """Base class for Invisibles-related exceptions.

    This exception serves as the base for all Invisibles-related errors,
    allowing for specific error types to inherit from it. It provides
    a common interface for handling Invisibles errors in a consistent manner.
    """

    pass


class InvisiblesConnectionError(InvisiblesError):
    """Exception raised when Invisibles connection operations fail.

    This exception indicates failures during connection management, which
    can include:
    - Connection establishment failures
    - Network connectivity issues
    - Server unavailability
    - Connection configuration errors
    """

    pass


class InvisiblesOperationError(InvisiblesError):
    """Exception raised when Invisibles remote operations fail.

    This exception indicates failures during remote operation execution, which
    can include:
    - Remote method call failures
    - Resource resolution failures
    - Serialization/deserialization errors
    - Remote server errors
    """

    pass


class InvisiblesServerError(InvisiblesError):
    """Exception raised when Invisibles server operations fail.

    This exception indicates failures on the server side, which
    can include:
    - Resource creation failures
    - Server configuration errors
    - Resource registry errors
    - Server lifecycle management errors
    """

    pass
