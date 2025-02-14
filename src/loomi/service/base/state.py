"""
Service lifecycle state management.

This module defines the possible states a service can be in throughout
its lifecycle. It provides a single enum class that tracks the progression
from creation through initialization, operation, and shutdown.
"""

from __future__ import annotations

from enum import Enum, auto

__all__ = [
    "ServiceState",
]


class ServiceState(Enum):
    """
    Enumeration of possible service lifecycle states.

    States:
        CREATED: Initial state after instance creation
        INITIALIZING: Service is starting up
        INITIALIZED: Service is ready for operation
        SHUTTING_DOWN: Service is in the process of shutting down
        SHUTDOWN: Service has completed shutdown
        ERROR: Service encountered an error

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


__all__ = [
    "ServiceState",
]
