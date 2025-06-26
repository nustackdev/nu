# """
# Complete RemoteResourceProxy implementation using SyncResource + wrapt.ObjectProxy.

# This provides transparent remote resource access with proper lifecycle management
# using existing Loomi patterns (UseService) and proven proxying (wrapt).
# """

# from __future__ import annotations

# from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

# import wrapt

# from loomi.attr import UseService
# from loomi.spec import Spec, SpecField

# from .exceptions import ResourceError
# from .logger import logger
# from .resource import SyncResource

# if TYPE_CHECKING:
#     pass

# __all__ = ["RemoteClientProtocol", "RemoteResourceProxy"]


# @runtime_checkable
# class RemoteClientProtocol(Protocol):
#     """
#     Protocol that remote clients must implement.

#     Remote clients should be Loomi resources (inherit from SyncResource)
#     to participate in proper lifecycle management.
#     """

#     def get_remote_resource(self, spec: Spec) -> Any:
#         """
#         Get a remote resource using the provided spec.

#         Args:
#             spec: Local resource specification (without remote config)

#         Returns:
#             Remote resource instance (RPyC netref, HTTP stub, etc.)

#         Raises:
#             Exception: If remote resource cannot be retrieved
#         """
#         ...

#     def is_connected(self) -> bool:
#         """
#         Check if client is connected and ready.

#         Returns:
#             True if connected and can serve requests
#         """
#         ...


# class RemoteResourceProxy(SyncResource, wrapt.ObjectProxy):
#     """
#     Transparent proxy for remote resources.

#     Combines SyncResource (for Loomi lifecycle) with wrapt.ObjectProxy
#     (for transparent method forwarding). Uses UseService to automatically
#     manage client dependencies and lifecycle.

#     The proxy coordinates initialization/shutdown between:
#     1. Local proxy resource (handled by SyncResource)
#     2. Remote client (handled by UseService)
#     3. Remote resource (coordinated manually)
#     """

#     # Client dependency - UseService handles sharing and lifecycle
#     client: RemoteClientProtocol = UseService()

#     def __init__(self, client_spec: Spec, resource_spec: Spec):
#         """
#         Initialize the remote resource proxy.

#         Args:
#             spec: Proxy specification containing client spec and local spec
#         """

#         # Initialize wrapt.ObjectProxy with None (will set __wrapped__ later in initialize())
#         wrapt.ObjectProxy.__init__(self, None)

#         # Initialize SyncResource
#         SyncResource.__init__(self, self._client_spec)

#         self._client_spec = client_spec
#         self._resource_spec = resource_spec

#         logger.debug(f"Created remote resource proxy for {self._resource_spec}")

#     def setup(self) -> None:
#         """
#         Setup the proxy resource.

#         This is called during resource initialization. At this point,
#         the client dependency has been resolved by UseService.
#         """

#         try:
#             logger.debug(f"Getting remote resource via client for {self._resource_spec}")

#             # Phase 2: Get the remote resource via client
#             self.__wrapped__ = self.client.get_remote_resource(self._resource_spec)

#             if self.__wrapped__ is None:
#                 raise ResourceError("Client returned None for remote resource")

#             # Phase 3: Initialize the remote resource if it supports initialization
#             if hasattr(self.__wrapped__, "initialize"):
#                 # Check if remote resource tracks initialization state
#                 if hasattr(self.__wrapped__, "is_initialized"):
#                     if not self.__wrapped__.is_initialized:
#                         logger.debug(f"Initializing remote resource {self._resource_spec}")
#                         self.__wrapped__.initialize()
#                     else:
#                         logger.debug(f"Remote resource {self._resource_spec} already initialized")
#                 else:
#                     # Remote doesn't track state - call initialize anyway (should be idempotent)
#                     logger.debug(
#                         f"Initializing remote resource {self._resource_spec} (no state tracking)"
#                     )
#                     self.__wrapped__.initialize()

#             logger.info(f"Successfully initialized remote resource proxy for {self._resource_spec}")

#         except Exception as e:
#             logger.error(f"Failed to initialize remote resource {self._resource_spec}: {e}")
#             # Clear wrapped object on failure
#             self.__wrapped__ = None
#             raise ResourceError("Failed to initialize remote resource") from e

#     def cleanup(self) -> None:
#         """
#         Cleanup the proxy resource.

#         Client cleanup is handled automatically by UseService dependency management.
#         """

#         try:
#             # Phase 1: Shutdown remote resource if it supports shutdown
#             if self.__wrapped__ and hasattr(self.__wrapped__, "shutdown"):
#                 # Check if remote resource tracks initialization state
#                 if hasattr(self.__wrapped__, "is_initialized"):
#                     if self.__wrapped__.is_initialized:
#                         logger.debug(f"Shutting down remote resource {self._resource_spec}")
#                         self.__wrapped__.shutdown()
#                     else:
#                         logger.debug(
#                             f"Remote resource {self._resource_spec} not initialized, skipping shutdown"
#                         )
#                 else:
#                     # Remote doesn't track state - try shutdown anyway
#                     try:
#                         logger.debug(
#                             f"Shutting down remote resource {self._resource_spec} (no state tracking)"
#                         )
#                         self.__wrapped__.shutdown()
#                     except Exception as e:
#                         logger.warning(f"Remote shutdown failed (might be expected): {e}")

#             logger.info(f"Successfully shut down remote resource proxy for {self._resource_spec}")

#         except Exception as e:
#             logger.error(f"Error shutting down remote resource {self._resource_spec}: {e}")
#             # Continue with proxy shutdown even if remote shutdown failed

#         finally:
#             # Phase 2: Clear wrapped object
#             self.__wrapped__ = None

#             # Phase 3: Shutdown the proxy itself (this also handles client cleanup via UseService)
#             super().shutdown()


# # Enhanced Spec class with remote capabilities
# class RemoteResourceProxySpec(Spec):
#     """
#     Specification for RemoteResourceProxy.

#     Contains both the client specification (for UseService dependency)
#     and the local resource specification (for remote creation).
#     """

#     factory: type = SpecField(default=RemoteResourceProxy)

#     # Client specification - becomes UseService dependency
#     client: Spec = SpecField()


# # Enhanced ResourceMeta integration
# def create_remote_resource(spec: Spec, is_dependency: bool) -> RemoteResourceProxy:
#     """
#     Create a remote resource using RemoteResourceProxy.

#     This function should be called from ResourceMeta.__call__() when
#     a remote resource is detected.

#     Args:
#         spec: Remote resource specification
#         is_dependency: Whether resource is being created as dependency

#     Returns:
#         RemoteResourceProxy instance
#     """
#     logger.debug(f"Creating remote resource: {spec}")

#     # Create proxy specification
#     client_spec = spec.get_remote_spec()
#     local_spec = spec.get_local_spec()

#     # Create proxy spec with client as UseService dependency
#     proxy_spec = RemoteResourceProxySpec(
#         client=client_spec,
#     )

#     # Create the proxy using normal resource creation
#     # This leverages all existing Loomi systems (registry, dependencies, etc.)
#     proxy = RemoteResourceProxy(proxy_spec, local_spec)

#     return proxy

"""
Simplified split: RemoteResourceManager + RemoteResourceProxy

1. Manager: SyncResource that handles client dependency and remote resource lifecycle
2. Proxy: Minimal wrapt.ObjectProxy with manager in slots
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

import wrapt

from loomi.attr import UseService
from loomi.spec import Spec, SpecField

from .resource import SyncResource

if TYPE_CHECKING:
    pass

__all__ = ["RemoteClientProtocol", "RemoteResourceManager", "RemoteResourceProxy"]


@runtime_checkable
class RemoteClientProtocol(Protocol):
    """Protocol that remote clients must implement."""

    def get_remote_resource(self, spec: Spec) -> Any:
        """Get a remote resource using the provided spec."""
        ...

    def is_connected(self) -> bool:
        """Check if client is connected and ready."""
        ...


class RemoteResourceManager(SyncResource):
    """
    Manages remote resource lifecycle and client dependencies.

    Simple SyncResource that:
    - Has client as UseService dependency
    - Gets remote resource in setup()
    - Cleans up remote resource in cleanup()
    """

    client: RemoteClientProtocol = UseService()

    spec: RemoteResourceManagerSpec

    def setup(self) -> None:
        """Get and initialize remote resource."""
        self.remote_resource = self.client.get_remote_resource(self.spec.resource_spec)

        if hasattr(self.remote_resource, "initialize"):
            if not getattr(self.remote_resource, "is_initialized", False):
                self.remote_resource.initialize()

    def cleanup(self) -> None:
        """Shutdown remote resource."""
        if self.remote_resource and hasattr(self.remote_resource, "shutdown"):
            if getattr(self.remote_resource, "is_initialized", True):
                self.remote_resource.shutdown()
        self.remote_resource = None


class RemoteResourceProxy(wrapt.ObjectProxy):
    """
    Minimal proxy that forwards to remote resource via manager.

    Uses slots to only store manager, inherits all proxy behavior from wrapt.
    """

    __slots__ = (
        "__wrapped__",
        "__self_manager__",
    )

    def __init__(self, manager: RemoteResourceManager):
        # Initialize manager and get remote resource
        manager.initialize()
        remote_resource = manager.remote_resource

        # Initialize wrapt with the remote resource
        super().__init__(remote_resource)

        # Store manager for lifecycle
        self.__self_manager__ = manager

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.__self_manager__.shutdown()


# Simple spec for manager
class RemoteResourceManagerSpec(Spec):
    factory: type = SpecField(default=RemoteResourceManager)
    resource_spec: Spec = SpecField()
    client: Spec = SpecField()


# Simple factory function
def create_remote_resource_proxy(spec: Spec) -> RemoteResourceProxy:
    """Create remote resource proxy."""

    # Create proxy specification
    client_spec = spec.get_remote_spec()
    resource_spec = spec.get_local_spec()

    manager_spec = RemoteResourceManagerSpec(resource_spec=resource_spec, client=client_spec)
    manager = RemoteResourceManager(manager_spec)
    return RemoteResourceProxy(manager)
