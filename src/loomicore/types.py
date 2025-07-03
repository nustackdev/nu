from __future__ import annotations

from enum import Enum, auto

__all__ = [
    "ResourceState",
]


class ResourceState(Enum):
    """
    Enumeration of possible resource lifecycle states.

    States:
        CREATED: Initial state after instance creation
        INITIALIZING: Resource is starting up
        INITIALIZED: Resource is ready for operation
        SHUTTING_DOWN: Resource is in the process of shutting down
        SHUTDOWN: Resource has completed shutdown
        ERROR: Resource encountered an error

    Notes:
        - States generally progress in order but may skip states on errors
        - ERROR state can be entered from any other state
    """

    CREATED = auto()
    INITIALIZING = auto()
    INITIALIZED = auto()
    SHUTTING_DOWN = auto()
    SHUTDOWN = auto()
    ERROR = auto()
