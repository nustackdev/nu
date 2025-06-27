from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

if TYPE_CHECKING:
    from loomi._lib.resource.spec import Spec

__all__ = [
    "RemoteClientProtocol",
]


@runtime_checkable
class RemoteClientProtocol(Protocol):
    """Protocol that remote clients must implement."""

    def get_remote_resource(self, spec: "Spec") -> Any:
        """Get a remote resource using the provided spec."""
        ...

    def is_connected(self) -> bool:
        """Check if client is connected and ready."""
        ...
