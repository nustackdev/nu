"""RPyC client service for connecting to remote EveryFlow resources.

This module provides client services that leverage EveryFlow's resource system
with Attach to automatically attach connection services. The client uses
the connection abstractions to communicate with remote RPyC servers.
"""

from __future__ import annotations

import pickle
from logging import getLogger
from typing import TYPE_CHECKING, cast

import attrs
from link import Attach, ResourceSpec, Spec, SyncResource

from ..exceptions import RPyCConnectionError, RPyCOperationError
from .tcp_conn import RPyCTCPConnectionSpec
from .unix_conn import RPyCUnixConnectionSpec


if TYPE_CHECKING:
    from ..factory import ResourceFactory
    from ..types import ResourceRegistry
    from .base_conn import BaseRPyCConnection


__all__ = [
    "RPyCClient",
    "RPyCTCPClientSpec",
    "RPyCUnixClientSpec",
]
logger = getLogger(__name__)


class RPyCClient(SyncResource):
    """Base class for RPyC client services.

    This class provides common client functionality.
    """

    connection: BaseRPyCConnection = Attach()

    @property
    def is_connected(self) -> bool:
        """Check if client is connected to RPyC server.

        Returns:
            True if connection is active
        """
        return self.connection.is_connected

    @property
    def root(self) -> ResourceFactory:
        """Get the root RPyC connection.

        Returns:
            RPyC root connection instance

        Raises:
            RPyCConnectionError: If not connected
        """
        if not self.is_connected:
            raise RPyCConnectionError("RPyC client is not connected")
        return cast("ResourceFactory", self.connection.get_connection.root)

    def get_proxy(self, spec: Spec) -> object:
        """Get a remote resource instance via RPyC.

        This is the main method for getting remote resources. It ensures
        we're connected and then uses the connection to get the resource.

        Args:
            spec: Specification of the resource to get remotely

        Returns:
            Remote resource instance (RPyC proxy)

        Raises:
            RPyCConnectionError: If not connected
            RPyCOperationError: If resource resolution fails
        """
        if not self.is_connected:
            raise RPyCConnectionError("RPyC client is not connected")

        try:
            remote_resource = self.root.exposed_get_resource(self._serialize_spec(spec))
            logger.debug(f"Retrieved remote resource: {spec}")
            return remote_resource

        except Exception as e:
            logger.error(f"Failed to get remote resource {spec}: {e}")
            raise RPyCOperationError(f"Failed to get remote resource {spec}") from e

    def list_remote_resources(self) -> ResourceRegistry:
        """List all active resources on the remote server.

        Returns:
            Dict mapping resource keys to factory names

        Raises:
            RPyCConnectionError: If not connected
            RPyCOperationError: If listing fails
        """
        if not self.is_connected:
            raise RPyCConnectionError("RPyC client is not connected")

        try:
            return self.root.exposed_list_resources()
        except Exception as e:
            logger.error(f"Failed to list remote resources: {e}")
            raise RPyCOperationError("Failed to list remote resources") from e

    def remove_remote_resource(self, spec: Spec) -> bool:
        """Remove a resource from the remote server.

        Args:
            spec: Specification of resource to remove

        Returns:
            True if resource was removed, False if not found

        Raises:
            RPyCConnectionError: If not connected
            RPyCOperationError: If removal fails
        """
        if not self.is_connected:
            raise RPyCConnectionError("RPyC client is not connected")

        try:
            return self.root.exposed_remove_resource(self._serialize_spec(spec))
        except Exception as e:
            logger.error(f"Failed to remove remote resource {spec}: {e}")
            raise RPyCOperationError(f"Failed to remove remote resource {spec}") from e

    def ping(self) -> bool:
        """Ping the remote server to check connectivity.

        Returns:
            True if server responds, False otherwise
        """
        try:
            if not self.is_connected:
                return False

            response = self.root.exposed_ping()
            return response == "pong"
        except Exception as e:
            logger.debug(f"Ping failed: {e}")
            return False

    def get_server_info(self) -> dict:
        """Get information about the remote server.

        Returns:
            Dict containing server information

        Raises:
            RPyCConnectionError: If not connected
            RPyCOperationError: If request fails
        """
        if not self.is_connected:
            raise RPyCConnectionError("RPyC client is not connected")

        try:
            return self.root.exposed_get_factory_info()
        except Exception as e:
            logger.error(f"Failed to get server info: {e}")
            raise RPyCOperationError("Failed to get server info") from e

    @staticmethod
    def _serialize_spec(spec: Spec) -> bytes:
        """Serialize a Spec instance to bytes for remote transmission.

        Args:
            spec: The Spec instance to serialize

        Returns:
            Serialized bytes representation of the spec
        """
        return pickle.dumps(spec)


@attrs.define(frozen=True, slots=True, kw_only=True)
class RPyCTCPClientSpec(ResourceSpec):
    """Specification for TCP-based RPyC client."""

    name: str = "rpyc_tcp_client"
    factory: type = RPyCClient

    # Connection service configuration
    connection: Spec = attrs.field(factory=lambda: RPyCTCPConnectionSpec())


@attrs.define(frozen=True, slots=True, kw_only=True)
class RPyCUnixClientSpec(ResourceSpec):
    """Specification for Unix socket-based RPyC client."""

    name: str = "rpyc_unix_client"
    factory: type = RPyCClient

    # Connection service configuration
    connection: Spec = attrs.field(factory=lambda: RPyCUnixConnectionSpec())
