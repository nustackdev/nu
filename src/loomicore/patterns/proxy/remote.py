"""
Complete RemoteResourceProxy implementation using SyncResource + wrapt.ObjectProxy.

This provides transparent remote resource access with proper lifecycle management
using existing Loomi patterns (UseService) and proven proxying (wrapt).
"""

from __future__ import annotations

import attrs
import wrapt

from loomi.interfaces.remote.client import RemoteClientProtocol
from loomicore.resource import SyncResource
from loomicore.spec import RemoteSpec, Spec

from ..attach.descriptor import Attach

__all__ = [
    "RemoteResourceCoordinator",
    "RemoteResourceProxy",
]


class RemoteResourceCoordinator(SyncResource):
    """
    Manages remote resource lifecycle and client dependencies.

    Simple SyncResource that:
    - Has client as UseService dependency
    - Gets remote resource in setup()
    - Cleans up remote resource in cleanup()
    """

    client: RemoteClientProtocol = Attach()

    spec: RemoteResourceCoordinatorSpec

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
    Minimal proxy that forwards to remote resource via coordinator.

    Uses slots to only store coordinator, inherits all proxy behavior from wrapt.
    """

    __slots__ = (
        "__wrapped__",
        "__self_coordinator__",
    )

    def __init__(self, coordinator: RemoteResourceCoordinator):
        # Initialize coordinator and get remote resource
        coordinator.initialize()
        remote_resource = coordinator.remote_resource

        # Initialize wrapt with the remote resource
        super().__init__(remote_resource)

        # Store coordinator for lifecycle
        self.__self_coordinator__: RemoteResourceCoordinator = coordinator

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.__self_coordinator__.shutdown()

    def shutdown(self):
        """Shutdown the remote resource via coordinator."""
        self.__self_coordinator__.shutdown()


# Simple spec for coordinator
@attrs.define(frozen=True, slots=True, kw_only=True)
class RemoteResourceCoordinatorSpec(Spec):
    resource_spec: Spec
    client: Spec
    factory: type = RemoteResourceCoordinator


# Simple factory function
def create_remote_resource_proxy(spec: RemoteSpec) -> RemoteResourceProxy:
    """Create remote resource proxy."""

    # Create proxy specification
    client_spec = spec.client_spec
    resource_spec = spec.inner_spec

    coordinator_spec = RemoteResourceCoordinatorSpec(
        resource_spec=resource_spec, client=client_spec
    )
    coordinator = RemoteResourceCoordinator(coordinator_spec)
    return RemoteResourceProxy(coordinator)
