"""
Resource proxy providing transparent access to proxied resources.

This module provides the ResourceProxy class which implements the final layer
of the double proxying pattern. It wraps a ProxyCoordinator using wrapt.ObjectProxy
to provide completely transparent access to remote resources while handling
lifecycle management automatically.

The ResourceProxy is what users actually interact with when using proxy resources.
It provides the same interface as the underlying resource but handles all the
proxy coordination behind the scenes.
"""

from __future__ import annotations

from types import TracebackType
from typing import TYPE_CHECKING, Any, final

import wrapt

from .exceptions import ProxyLifecycleError
from .logger import logger

if TYPE_CHECKING:
    from .coordinator import ProxyCoordinator

__all__ = [
    "ResourceProxy",
]


class ResourceProxy(wrapt.ObjectProxy):
    """
    Transparent proxy wrapper providing access to proxied resources.

    ResourceProxy implements the final layer of the double proxying pattern,
    wrapping a ProxyCoordinator to provide completely transparent access to
    remote resources. It uses wrapt.ObjectProxy to inherit all proxy behavior
    while adding Loomi-specific lifecycle management.

    Key features:
    - Transparent method and attribute forwarding via wrapt.ObjectProxy
    - Automatic coordinator initialization and cleanup
    - Context manager support for automatic lifecycle management
    - Proper error handling and logging
    - Minimal overhead and clean separation of concerns

    The proxy appears identical to the underlying resource from the user's
    perspective, with all method calls and attribute access forwarded
    transparently through the proxy chain.

    Examples:
        Direct usage:
        >>> coordinator = ProxyCoordinator(proxy_spec)
        >>> proxy = ResourceProxy(coordinator)
        >>> result = proxy.some_method(args)  # Transparent forwarding
        >>> proxy.shutdown()

        Context manager usage:
        >>> with ResourceProxy(coordinator) as proxy:
        ...     result = proxy.some_method(args)
        # Automatic cleanup on exit

        Via factory function:
        >>> proxy = create_resource_proxy(proxy_spec)
        >>> with proxy:
        ...     result = proxy.some_method(args)

    Architecture:
        User Code
            ↓
        ResourceProxy (wrapt.ObjectProxy)
            ↓
        ProxyCoordinator (Loomi resource)
            ↓
        TransportClient (Attach dependency)
            ↓
        Transport Proxy (implementation-specific)
            ↓
        Remote Resource
    """

    # Use slots to ensure clean proxy behavior
    __slots__ = (
        "__wrapped__",  # wrapt.ObjectProxy requirement
        "__self_coordinator__",  # Our coordinator reference
    )

    @final
    def __init__(self, coordinator: "ProxyCoordinator") -> None:
        """
        Initialize resource proxy with coordinator.

        Creates a transparent proxy wrapper around the given ProxyCoordinator.
        The coordinator is initialized automatically and the transport proxy
        is retrieved for transparent method forwarding.

        Args:
            coordinator: ProxyCoordinator instance to wrap

        Raises:
            ProxyLifecycleError: If coordinator initialization fails
            TypeError: If coordinator is not a ProxyCoordinator instance

        Notes:
            - Coordinator is initialized automatically during construction
            - Transport proxy is retrieved and used as the wrapped object
            - Coordinator reference is stored for lifecycle management
            - All method calls are forwarded transparently via wrapt
        """
        logger.debug(f"Creating ResourceProxy for coordinator: {coordinator.readable_name}")

        try:
            # Initialize coordinator to get transport proxy
            coordinator.initialize()

            # Get the transport proxy for transparent forwarding
            transport_proxy = coordinator.proxy

            logger.debug(
                f"Retrieved transport proxy for ResourceProxy: {coordinator.readable_name}"
            )

            # Initialize wrapt.ObjectProxy with the transport proxy
            # This enables transparent method and attribute forwarding
            super().__init__(transport_proxy)

            # Store coordinator reference for lifecycle management
            # Use name mangling to avoid conflicts with proxied attributes
            self.__self_coordinator__: ProxyCoordinator = coordinator

            logger.info(f"Successfully created ResourceProxy: {coordinator.readable_name}")

        except Exception as e:
            logger.error(f"Failed to create ResourceProxy for {coordinator.readable_name}: {e}")

            # Ensure coordinator is cleaned up on failure
            try:
                if hasattr(coordinator, "shutdown"):
                    coordinator.shutdown()
            except Exception as cleanup_error:
                logger.warning(
                    f"Error during cleanup after failed ResourceProxy creation: {cleanup_error}"
                )

            raise ProxyLifecycleError(
                f"Failed to create ResourceProxy for {coordinator.readable_name}"
            ) from e

    # === Context Manager Support ===

    def __enter__(self) -> "ResourceProxy":
        """
        Enter context manager.

        The coordinator is already initialized during construction, so this
        method just returns self for use within the context block.

        Returns:
            Self for use within context

        Notes:
            - Coordinator is already initialized
            - Resource is ready for immediate use
            - Cleanup will be handled automatically on exit
        """
        logger.debug(
            f"Entering context for ResourceProxy: {self.__self_coordinator__.readable_name}"
        )
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """
        Exit context manager and cleanup coordinator.

        Automatically shuts down the coordinator when exiting the context,
        ensuring proper cleanup of all proxy resources. This includes
        transport client disconnection and optional server shutdown.

        Args:
            exc_type: Exception type if exception occurred
            exc_val: Exception instance if exception occurred
            exc_tb: Exception traceback if exception occurred

        Notes:
            - Cleanup occurs regardless of whether exceptions happened
            - All coordinator resources are cleaned up
            - Shutdown errors are logged but don't suppress original exceptions
        """
        logger.debug(
            f"Exiting context for ResourceProxy: {self.__self_coordinator__.readable_name}"
        )

        try:
            self.shutdown()
        except Exception as e:
            logger.warning(f"Error during ResourceProxy context exit: {e}")
            # Don't raise to avoid suppressing original exceptions

    # === Lifecycle Management ===

    def shutdown(self) -> None:
        """
        Shutdown the proxied resource and cleanup all resources.

        This method provides explicit lifecycle control for cases where
        context manager usage is not appropriate. It delegates to the
        coordinator's shutdown method to ensure proper cleanup.

        Raises:
            ProxyLifecycleError: If shutdown fails

        Notes:
            - Safe to call multiple times
            - Automatically handles all cleanup steps
            - Logs errors but attempts complete cleanup
            - Coordinator handles transport client/server cleanup
        """
        logger.info(f"Shutting down ResourceProxy: {self.__self_coordinator__.readable_name}")

        try:
            self.__self_coordinator__.shutdown()
            logger.debug(
                f"Successfully shut down ResourceProxy: {self.__self_coordinator__.readable_name}"
            )

        except Exception as e:
            logger.error(f"Error during ResourceProxy shutdown: {e}")
            raise ProxyLifecycleError(
                f"Failed to shutdown ResourceProxy for {self.__self_coordinator__.readable_name}"
            ) from e

    # === Status and Introspection ===

    @property
    def coordinator(self) -> "ProxyCoordinator":
        """
        Get the underlying ProxyCoordinator for advanced usage.

        Returns:
            ProxyCoordinator instance managing this proxy

        Notes:
            - Provides access to coordinator for advanced scenarios
            - Use with caution as it breaks abstraction
            - Mainly for debugging and introspection
        """
        return self.__self_coordinator__

    def __repr__(self) -> str:
        """
        String representation for debugging.

        Returns:
            String showing proxy state and coordinator information
        """
        coordinator_name = self.__self_coordinator__.readable_name
        return f"<ResourceProxy '{coordinator_name}'>"

    # === Special Method Handling ===

    def __getstate__(self) -> dict[str, Any]:
        """
        Handle pickle serialization.

        ResourceProxy instances are not serializable due to their connection
        state and complex internal structure. This method raises an error
        to prevent accidental serialization attempts.

        Raises:
            TypeError: ResourceProxy instances cannot be pickled

        Notes:
            - Proxy resources maintain active connections
            - Serialization would break connection state
            - Use specs for serializable resource configuration
        """
        raise TypeError(
            "ResourceProxy instances cannot be pickled. "
            "Use ProxySpec for serializable resource configuration."
        )

    def __setstate__(self, state: dict[str, Any]) -> None:
        """
        Handle pickle deserialization.

        ResourceProxy instances are not serializable, so this method
        raises an error to prevent deserialization attempts.

        Args:
            state: Pickled state (not used)

        Raises:
            TypeError: ResourceProxy instances cannot be pickled
        """
        raise TypeError(
            "ResourceProxy instances cannot be unpickled. "
            "Use ProxySpec for serializable resource configuration."
        )

    # Note: All other method calls and attribute access are handled
    # transparently by wrapt.ObjectProxy and forwarded to the transport proxy
