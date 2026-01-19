"""Multiprocessing launcher exceptions.

This module defines exceptions specific to multiprocessing launcher operations,
providing clear error types for different subprocess and IPC failure scenarios.
"""

from __future__ import annotations

from ..exceptions import LauncherError


__all__ = [
    "HostStartupError",
    "MultiprocessingLauncherError",
    "ProcessCreationError",
    "ProcessStartupError",
    "ProcessTerminationError",
    "ProcessTimeoutError",
]


class MultiprocessingLauncherError(LauncherError):
    """Base exception for multiprocessing launcher errors."""

    pass


class ProcessCreationError(MultiprocessingLauncherError):
    """Exception raised when subprocess creation fails.

    Examples:
        - Insufficient system resources
        - Permission errors
        - Invalid process configuration
    """

    pass


class ProcessStartupError(MultiprocessingLauncherError):
    """Exception raised when subprocess startup fails.

    Examples:
        - Process crashes during startup
        - Import errors in worker module
        - Signal handling setup failures
    """

    pass


class ProcessTimeoutError(MultiprocessingLauncherError):
    """Exception raised when process operations timeout.

    Examples:
        - Server startup timeout
        - Process shutdown timeout
        - IPC communication timeout
    """

    pass


class HostStartupError(MultiprocessingLauncherError):
    """Exception raised when host/server startup fails within subprocess.

    Examples:
        - Server bind failures
        - Invalid host specification
        - Resource allocation failures
    """

    pass


class ProcessTerminationError(MultiprocessingLauncherError):
    """Exception raised when subprocess termination fails.

    Examples:
        - Process doesn't respond to termination signals
        - Cleanup failures
        - Zombie process creation
    """

    pass
