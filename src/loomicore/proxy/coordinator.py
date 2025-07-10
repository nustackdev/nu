"""
Proxy coordinator for managing proxy resource lifecycle.

This module provides the ProxyCoordinator class, which is the main component
of the proxy system. It handles the complete lifecycle of proxy resources,
including optional server spawning, transport client management, and method
delegation to transport-specific proxy objects.

The coordinator implements the double proxying pattern where it manages
Loomi-specific lifecycle concerns while delegating actual method calls to
transport-specific proxy implementations.
"""

from __future__ import annotations

from typing import Any

import attrs

from loomicore.attach import Attach
from loomicore.resource import SyncResource
from loomicore.spec import Spec

from .exceptions import ProxyLifecycleError
from .logger import logger
from .transport import TransportClientProtocol

__all__ = [
    "ProxyCoordinator",
    "ProxyCoordinatorSpec",
]


class ProxyCoordinator(SyncResource):
    """
    Main coordinator for proxy resource lifecycle management.

    The ProxyCoordinator is the central component of the proxy system that
    provides Loomi integration while delegating actual method calls to
    transport-specific proxy objects. It implements the double proxying
    pattern where it handles lifecycle concerns (setup, teardown, server
    spawning) while the transport proxy handles method forwarding.

    Key responsibilities:
    - Optional server auto-spawning via Attach descriptor
    - Transport client creation and connection via Attach descriptor
    - Transport proxy retrieval and caching
    - Method delegation via proxy property
    - Cleanup sequencing and error handling
    - Full Loomi lifecycle integration

    The coordinator appears as a regular Loomi resource to users and
    integrates seamlessly with existing Loomi patterns like Attach,
    lifecycle management, and resource deduplication.

    Examples:
        Basic usage:
        >>> coordinator = ProxyCoordinator(proxy_spec)
        >>> coordinator.initialize()
        >>> result = coordinator.proxy.some_method(args)
        >>> coordinator.shutdown()

        Context manager usage:
        >>> with ProxyCoordinator(proxy_spec) as coordinator:
        ...     result = coordinator.proxy.some_method(args)

        Via Attach pattern:
        >>> class MyService(SyncResource):
        ...     proxy = Attach(ProxySpec(...))
        ...     def do_work(self):
        ...         return self.proxy.some_method(args)
    """

    spec: ProxyCoordinatorSpec

    launcher: Any = Attach(optional=True)

    client: TransportClientProtocol = Attach()

    def setup(self) -> None:
        """
        Initialize the proxy coordinator and establish proxy connection.

        This method handles the complete initialization sequence:
        1. Validates configuration and prerequisites
        2. Dependencies (client/server) are automatically resolved by Loomi
        3. Transport client connection establishment
        4. Transport proxy retrieval and caching
        5. State tracking and error handling

        The method is idempotent - calling it on an already initialized
        coordinator is safe and will not cause duplicate initialization.

        Raises:
            ProxyLifecycleError: If initialization fails at any step
            ProxyConnectionError: If transport connection fails
            ProxyConfigurationError: If configuration is invalid

        Notes:
            - Called automatically by Loomi lifecycle management
            - Dependencies (client/server) are resolved by Attach descriptors
            - All transport errors are wrapped in appropriate proxy exceptions
        """
        logger.info(f"Initializing ProxyCoordinator: '{self.readable_name}'")

        self._transport_proxy: Any = None

        try:
            # Retrieve transport proxy from connected client
            logger.debug(f"Retrieving transport proxy for '{self.readable_name}'")
            self._transport_proxy = self.client.get_proxy(self.spec.resource_spec)

            if self._transport_proxy is None:
                raise ProxyLifecycleError(
                    f"Transport client returned None proxy for '{self.readable_name}'"
                )

            logger.debug(f"Successfully retrieved transport proxy for '{self.readable_name}'")

            # Step 3: Initialize transport proxy if it supports initialization
            if hasattr(self._transport_proxy, "initialize"):
                logger.debug(f"Initializing transport proxy for '{self.readable_name}'")
                self._transport_proxy.initialize()

            logger.info(f"Successfully initialized ProxyCoordinator: '{self.readable_name}'")

        except Exception as e:
            # Clean up any partial initialization on failure
            self._cleanup_on_error()

            logger.error(f"Failed to initialize ProxyCoordinator '{self.readable_name}': {e}")
            raise ProxyLifecycleError(
                f"Failed to initialize ProxyCoordinator '{self.readable_name}'"
            ) from e

    def cleanup(self) -> None:
        """
        Shutdown the proxy coordinator and clean up all resources.

        This method handles the complete shutdown sequence:
        1. Validates current state
        2. Transport proxy shutdown (if supported)
        3. Transport client disconnection (client managed by Loomi)
        4. Optional server shutdown (server managed by Loomi)
        5. State cleanup and error handling

        The method handles partial shutdown gracefully and is safe to call
        multiple times. It attempts to complete all cleanup steps even if
        some fail, logging errors but not raising exceptions.

        Notes:
            - Called automatically by Loomi lifecycle management
            - Dependencies (client/server) are cleaned up by Loomi
            - Errors during shutdown are logged but don't raise exceptions
            - Cleanup is attempted in reverse initialization order
        """
        logger.info(f"Shutting down ProxyCoordinator: '{self.readable_name}'")

        # Shutdown transport proxy first
        self._cleanup_transport_proxy()

        # Note: Client and server cleanup is handled by Loomi via Attach descriptors
        # This includes disconnect() and stop() calls respectively

        logger.info(f"Successfully shut down ProxyCoordinator: '{self.readable_name}'")

    @property
    def proxy(self) -> Any:
        """
        Get the transport proxy for method delegation.

        This property retrieves the transport proxy from the connected
        transport client. It is used by ResourceProxy to forward method
        calls to the actual transport-specific implementation.

        Returns:
            The transport proxy object that implements the required methods

        Notes:
            - Only available after successful initialization
            - Used by ResourceProxy for method forwarding
            - Transport proxy handles actual method calls and attribute access
        """

        return self._transport_proxy

    def _cleanup_on_error(self) -> None:
        """
        Clean up partial initialization on error.

        This method is called when initialization fails to clean up any
        resources that were partially initialized. It ensures no resources
        are leaked when initialization fails.

        Notes:
            - Called automatically on initialization failure
            - Attempts all cleanup steps even if some fail
            - Logs errors but doesn't raise exceptions
        """
        logger.debug(f"Cleaning up partial initialization for '{self.readable_name}'")

        self._cleanup_transport_proxy()

        # Note: Client and server cleanup is handled by Loomi automatically
        # via Attach descriptors if initialization fails

    def _cleanup_transport_proxy(self) -> None:
        """
        Clean up transport proxy.

        Attempts to shutdown the transport proxy if it supports shutdown,
        then clears the reference. This ensures proper cleanup of transport
        resources and prevents resource leaks.

        Notes:
            - Safe to call multiple times
            - Attempts shutdown if proxy supports it
            - Logs warnings for cleanup errors but doesn't raise
        """
        if self._transport_proxy is not None:
            logger.debug(f"Cleaning up transport proxy for '{self.readable_name}'")

            # Attempt to shutdown transport proxy if it supports it
            try:
                if hasattr(self._transport_proxy, "shutdown"):
                    logger.debug(f"Shutting down transport proxy for '{self.readable_name}'")
                    self._transport_proxy.shutdown()
            except Exception as e:
                logger.warning(
                    f"Error shutting down transport proxy for '{self.readable_name}': {e}"
                )
            finally:
                # Always clear reference
                self._transport_proxy = None


@attrs.define(frozen=True, slots=True, kw_only=True)
class ProxyCoordinatorSpec(Spec):
    """
    Specification for ProxyCoordinator.

    This class defines the specification for creating ProxyCoordinator
    instances.
    """

    factory: type = ProxyCoordinator
    name: str = "proxy_coordinator"

    resource_spec: Spec
    launcher: Spec | None = None
    client: Spec
