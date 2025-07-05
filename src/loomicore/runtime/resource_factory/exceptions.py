from __future__ import annotations

from loomicore.exceptions import ResourceError

__all__ = [
    "CreationError",
]


class CreationError(ResourceError):
    """
    Exception raised when resource creation fails.

    This exception indicates failures during resource instantiation, which
    can include:
    - Invalid constructor arguments
    - Resource allocation failures
    - Dependency resolution failures
    - Initialization errors

    Note:
        This exception does not inherit from ResourceError since it may occur
        before the resource is fully constructed.
    """

    pass
