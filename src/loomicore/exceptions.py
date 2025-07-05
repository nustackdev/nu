"""
Resource-related exceptions for error handling.
"""

from __future__ import annotations

__all__ = [
    "ResourceError",
]


class ResourceError(Exception):
    """
    Base class for resource-related exceptions.

    This exception serves as the base for all resource-related errors,
    allowing for specific error types to inherit from it. It provides
    a common interface for handling resource errors in a consistent manner.
    """

    pass
