"""
Complete RemoteResourceProxy implementation using SyncResource + wrapt.ObjectProxy.

This provides transparent remote resource access with proper lifecycle management
using existing Loomi patterns (UseService) and proven proxying (wrapt).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

import wrapt

from loomi.attr import UseService
from loomi.spec import Spec, SpecField

from .resource import SyncResource

if TYPE_CHECKING:
    pass

__all__ = [
    "RemoteClientProtocol",
    "RemoteResourceManager",
    "RemoteResourceProxy",
]


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
