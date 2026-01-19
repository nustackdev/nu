"""Type definitions for multiprocessing launcher.

This module defines types and protocols used for inter-process communication
and coordination between the launcher and worker subprocess.
"""

from __future__ import annotations

from collections import namedtuple
from enum import Enum


__all__ = [
    "ProcessState",
    "StartupResult",
    "StartupStatus",
]


class ProcessState(Enum):
    """States of the worker process lifecycle."""

    CREATED = "created"
    STARTING = "starting"
    READY = "ready"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


class StartupStatus(Enum):
    """Status values for startup result messages."""

    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"


# Named tuple for startup results from subprocess
StartupResult = namedtuple(
    "StartupResult",
    [
        "status",  # StartupStatus
        "connection_info",  # ConnectionInfo | None
        "error_message",  # str | None
        "pid",  # int
    ],
)
