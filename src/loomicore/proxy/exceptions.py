"""
Exception classes for the proxy system.

This module defines the exception hierarchy for proxy-related errors,
providing specific exception types for different failure scenarios in
the proxy system. The exceptions form a clear hierarchy that allows
for both specific and general error handling as needed.

The exception hierarchy is designed to provide detailed context about
failures while maintaining compatibility with Loomi's existing error
handling patterns.
"""

from __future__ import annotations

from loomicore.exceptions import ResourceError

__all__ = [
    "ProxyError",
    "ProxyConfigurationError",
    "ProxyConnectionError",
    "ProxyLifecycleError",
    "ProxyOperationError",
    "TransportError",
]


class ProxyError(ResourceError):
    """
    Base exception for proxy-related errors.

    This exception serves as the base for all proxy-related errors,
    allowing for specific error types to inherit from it while providing
    a common interface for handling proxy errors in a consistent manner.

    All proxy system exceptions inherit from this base class, enabling
    users to catch all proxy-related errors with a single exception type
    while still allowing for specific error handling when needed.
    """

    pass


class ProxyConfigurationError(ProxyError):
    """
    Exception raised when proxy configuration is invalid.

    This exception indicates failures during proxy configuration validation
    or setup, which can include:
    - Invalid ProxySpec configuration
    - Missing required transport client or server specifications
    - Incompatible transport configurations
    - Invalid multi-level wrapping configurations

    Examples:
        - ProxySpec missing client_spec
        - Transport client configuration referencing non-existent servers
        - Circular proxy wrapping specifications
    """

    pass


class ProxyConnectionError(ProxyError):
    """
    Exception raised when proxy connection operations fail.

    This exception indicates failures during connection establishment
    or management between proxy coordinators and transport clients,
    which can include:
    - Transport client connection failures
    - Network connectivity issues
    - Server unavailability
    - Authentication or authorization failures

    Examples:
        - TCP connection refused by server
        - Unix socket file not found
        - Ray cluster not accessible
        - HTTP server returning error status codes
    """

    pass


class ProxyLifecycleError(ProxyError):
    """
    Exception raised when proxy lifecycle operations fail.

    This exception indicates failures during proxy coordinator lifecycle
    management, which can include:
    - Server auto-spawning failures
    - Coordinator initialization failures
    - Resource cleanup failures
    - Lifecycle state transition errors

    Examples:
        - Server fails to start during auto-spawn
        - Transport client fails to initialize
        - Cleanup operations encounter errors
        - Coordinator already initialized/shutdown
    """

    pass


class ProxyOperationError(ProxyError):
    """
    Exception raised when proxy operations fail.

    This exception indicates failures during proxy operation execution,
    which can include:
    - Transport proxy method call failures
    - Remote resource operation failures
    - Serialization/deserialization errors
    - Transport-specific operation errors

    Examples:
        - Remote method call raises exception
        - Network errors during method execution
        - Timeout during remote operation
        - Transport proxy returns error response
    """

    pass


class TransportError(ProxyError):
    """
    Exception raised when transport-specific operations fail.

    This exception indicates failures at the transport implementation
    level, which can include:
    - Transport protocol errors
    - Transport-specific configuration errors
    - Transport backend failures
    - Transport implementation bugs

    Examples:
        - RPyC protocol errors
        - Ray actor failures
        - HTTP transport errors
        - Custom transport implementation errors

    Notes:
        This exception is intended for transport implementations to raise
        when they encounter transport-specific errors that don't fit into
        the other proxy exception categories.
    """

    pass
