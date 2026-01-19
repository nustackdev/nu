"""Client for connecting to an Invisibles RPC server."""

from __future__ import annotations

import pickle
import time
from logging import getLogger
from typing import TYPE_CHECKING, Literal, cast, final

import attrs
from everylink import ResourceSpec, Spec, SyncResource
from invisibles import InvisiblesConnection
from invisibles.codec.micropack_codec import MicroPackCodec
from invisibles.config import ConnectionConfig
from netkit import SyncConnector
from netkit.framing import LengthPrefixedFraming
from netkit.transports import TCPTransport, UnixSocketTransport

from .exceptions import InvisiblesConnectionError, InvisiblesOperationError


if TYPE_CHECKING:
    from .factory import ResourceFactory, ResourceRegistry


logger = getLogger(__name__)


class InvisiblesClient(SyncResource):
    """Client for connecting to an Invisibles RPC server."""

    spec: InvisiblesClientSpec

    def _create_connection_impl(self) -> InvisiblesConnection:
        conn_type = self.spec.conn_type
        if conn_type == "tcp":
            return self._create_tcp_connection()
        elif conn_type == "unix":
            return self._create_unix_connection()
        else:
            raise ValueError(f"Unsupported connection type: {conn_type}")

    def _create_tcp_connection(self) -> InvisiblesConnection:
        logger.debug(f"Connecting to Invisibles server at {self.spec.host}:{self.spec.port}")

        # Connect via NetKit
        connector = SyncConnector(
            transport_factory=lambda: TCPTransport(),
            framing_factory=lambda t: LengthPrefixedFraming(t, max_frame_size=1024 * 1024),
        )

        address = self.spec.host
        port = self.spec.port

        logger.info(f"Connecting to {address}:{port}")
        netkit_conn = connector.connect(address=address, port=port, timeout=5.0)
        logger.info("Connected!")

        # Create Invisibles connection
        config = ConnectionConfig()
        config.connection_id = "client"
        codec = MicroPackCodec()

        # Client has no service (or could have one for bidirectional)
        invisibles_conn = InvisiblesConnection(
            netkit_connection=netkit_conn,
            codec=codec,
            root_service=None,  # Client doesn't expose a service
            config=config,
        )
        return invisibles_conn

    def _create_unix_connection(self) -> InvisiblesConnection:
        socket_path = self.spec.address
        logger.debug(f"Connecting to Invisibles server at {socket_path}")

        # Connect via NetKit
        connector = SyncConnector(
            transport_factory=lambda: UnixSocketTransport(),
            framing_factory=lambda t: LengthPrefixedFraming(t, max_frame_size=1024 * 1024),
        )

        logger.info(f"Connecting to {socket_path}")
        netkit_conn = connector.connect(socket_path, timeout=5.0)
        logger.info("Connected!")

        # Create Invisibles connection
        config = ConnectionConfig(connection_id="client")
        codec = MicroPackCodec()

        # Client has no service (or could have one for bidirectional)
        invisibles_conn = InvisiblesConnection(
            netkit_connection=netkit_conn,
            codec=codec,
            root_service=None,  # Client doesn't expose a service
            config=config,
        )
        return invisibles_conn

    @property
    def endpoint(self) -> str:
        """Get string representation of the TCP endpoint."""
        return (
            f"{self.spec.host}:{self.spec.port}"
            if self.spec.conn_type == "tcp"
            else self.spec.address
        )

    # --- Instance properties --- #

    @final
    @property
    def is_connected(self) -> bool:
        """Check if connected to Invisibles server.

        Returns:
            True if connection is active and healthy
        """
        return self._connected and self._connection is not None and self._connection.is_connected()

    @final
    @property
    def get_connection(self) -> InvisiblesConnection:
        """Get the underlying Invisibles connection for direct use.

        Returns:
            Invisibles connection instance

        Raises:
            InvisiblesConnectionError: If not connected
        """
        self._ensure_connected()
        return self._connection

    # --- Lifecycle methods --- #

    def setup(self) -> None:
        """Initialize the Invisibles connection service.

        Sets up internal state and optionally establishes connection
        based on auto_connect setting.
        """
        self._connection: InvisiblesConnection
        self._connected = False

        self.connect()

    def cleanup(self) -> None:
        """Clean up the Invisibles connection service.

        Ensures connection is properly closed and resources are freed.
        """
        if self.is_connected:
            self.disconnect()

    def _ensure_connected(self) -> None:
        """Verify connection state."""
        if not self._connected:
            raise InvisiblesConnectionError("Invisibles connection is not established")

    @final
    def connect(self, max_retries: int = 3, initial_delay: float = 0.1) -> None:
        """Establish connection to Invisibles server with retry logic.

        Args:
            max_retries: Maximum number of connection attempts
            initial_delay: Initial delay between retries (doubles each attempt)

        Raises:
            InvisiblesConnectionError: If connection fails after all retries
        """
        if self.is_connected:
            return  # Already connected

        delay = initial_delay
        last_error = None

        for attempt in range(max_retries):
            try:
                self._connection = self._create_connection_impl()
                self._connected = True
                logger.debug(f"Invisibles connection established to {self.endpoint}")
                return
            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    logger.debug(
                        f"Connection attempt {attempt + 1}/{max_retries} failed, "
                        f"retrying in {delay:.2f}s: {e}"
                    )
                    time.sleep(delay)
                    delay *= 2  # Exponential backoff
                else:
                    logger.debug(
                        f"Failed to connect to {self.endpoint} after {max_retries} attempts: {e}"
                    )

        raise InvisiblesConnectionError(
            f"Failed to connect to {self.endpoint} after {max_retries} attempts"
        ) from last_error

    @final
    def disconnect(self) -> None:
        """Close connection to Invisibles server.

        Properly closes the connection and cleans up resources.
        """
        if self._connection and self._connection.is_connected():
            try:
                self._connection.close()
                logger.debug(f"Disconnected from {self.endpoint}")
            except Exception as e:
                logger.debug(f"Error during disconnect from {self.endpoint}: {e}")
            finally:
                self._connected = False

    @property
    def root(self) -> ResourceFactory:
        """Get the root Invisibles connection.

        Returns:
            Invisibles root connection instance

        Raises:
            InvisiblesConnectionError: If not connected
        """
        from invisibles.core.consts import HANDLE_GET_ROOT

        if not self.is_connected:
            raise InvisiblesConnectionError("Invisibles client is not connected")
        return cast("ResourceFactory", self._connection.sync_request(HANDLE_GET_ROOT))

    def get_proxy(self, spec: Spec) -> object:
        """Get a remote resource instance via Invisibles.

        This is the main method for getting remote resources. It ensures
        we're connected and then uses the connection to get the resource.

        Args:
            spec: Specification of the resource to get remotely

        Returns:
            Remote resource instance (Invisibles proxy)

        Raises:
            InvisiblesConnectionError: If not connected
            InvisiblesOperationError: If resource resolution fails
        """
        if not self.is_connected:
            raise InvisiblesConnectionError("Invisibles client is not connected")

        try:
            remote_resource = self.root.exposed_get_resource(self._serialize_spec(spec))
            logger.debug(f"Retrieved remote resource: {spec}")
            return remote_resource

        except Exception as e:
            logger.error(f"Failed to get remote resource {spec}: {e}")
            raise InvisiblesOperationError(f"Failed to get remote resource {spec}") from e

    def list_remote_resources(self) -> ResourceRegistry:
        """List all active resources on the remote server.

        Returns:
            Dict mapping resource keys to factory names

        Raises:
            InvisiblesConnectionError: If not connected
            InvisiblesOperationError: If listing fails
        """
        if not self.is_connected:
            raise InvisiblesConnectionError("Invisibles client is not connected")

        try:
            return self.root.exposed_list_resources()
        except Exception as e:
            logger.error(f"Failed to list remote resources: {e}")
            raise InvisiblesOperationError("Failed to list remote resources") from e

    def remove_remote_resource(self, spec: Spec) -> bool:
        """Remove a resource from the remote server.

        Args:
            spec: Specification of resource to remove

        Returns:
            True if resource was removed, False if not found

        Raises:
            InvisiblesConnectionError: If not connected
            InvisiblesOperationError: If removal fails
        """
        if not self.is_connected:
            raise InvisiblesConnectionError("Invisibles client is not connected")

        try:
            return self.root.exposed_remove_resource(self._serialize_spec(spec))
        except Exception as e:
            logger.error(f"Failed to remove remote resource {spec}: {e}")
            raise InvisiblesOperationError(f"Failed to remove remote resource {spec}") from e

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
            InvisiblesConnectionError: If not connected
            InvisiblesOperationError: If request fails
        """
        if not self.is_connected:
            raise InvisiblesConnectionError("Invisibles client is not connected")

        try:
            return self.root.exposed_get_factory_info()
        except Exception as e:
            logger.error(f"Failed to get server info: {e}")
            raise InvisiblesOperationError("Failed to get server info") from e

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
class InvisiblesClientSpec(ResourceSpec):
    """Specification for creating an Invisibles RPC client."""

    factory: type = InvisiblesClient
    name: str = "invisibles_connection"
    conn_type: Literal["unix", "tcp"] = "unix"
    address: str = "./invisibles.sock"
    host: str = "localhost"
    port: int = 18812
