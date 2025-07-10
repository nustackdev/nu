"""
Launcher exceptions for error handling.

This module defines exceptions specific to launcher operations,
providing clear error types for different failure scenarios.
"""

from __future__ import annotations

__all__ = [
    "LauncherError",
    "LauncherConfigurationError",
    "LauncherProvisioningError",
    "LauncherOperationError",
]


class LauncherError(Exception):
    """Base exception for launcher-related errors."""

    pass


class LauncherConfigurationError(LauncherError):
    """
    Exception raised when launcher configuration is invalid.

    Examples:
        - Missing required configuration parameters
        - Invalid resource or host specifications
        - Incompatible launcher/host combinations
    """

    pass


class LauncherProvisioningError(LauncherError):
    """
    Exception raised when infrastructure provisioning fails.

    Examples:
        - Process creation failures
        - Container startup failures
        - Ray actor initialization failures
        - Resource allocation errors
    """

    pass


class LauncherOperationError(LauncherError):
    """
    Exception raised when launcher operations fail.

    Examples:
        - Host startup failures
        - Communication setup errors
        - Resource hosting failures
    """

    pass
