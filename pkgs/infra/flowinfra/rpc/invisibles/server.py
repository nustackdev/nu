"""Invisibles RPC server implementation."""

from __future__ import annotations

import socket
import threading
import time
from logging import getLogger
from typing import TYPE_CHECKING, Literal

import attrs
from link import ResourceSpec, SyncResource
from invisibles import InvisiblesConnection
from invisibles.codec.micropack_codec import MicroPackCodec
from invisibles.config import AttributeAccessConfig, ConnectionConfig
from netkit import SyncServer
from netkit.executors import ThreadPoolExecutor
from netkit.framing import LengthPrefixedFraming
from netkit.transports import TCPListener, UnixSocketListener

from .exceptions import InvisiblesServerError
from .factory import ResourceFactory


if TYPE_CHECKING:
    from netkit.core.connection import SyncConnection


logger = getLogger(__name__)


class InvisiblesServer(SyncResource):
    """Invisibles RPC server for EveryFlow resource management."""

    spec: InvisiblesServerSpec

    @property
    def endpoint(self) -> str:
        """Get string representation of the TCP endpoint."""
        return (
            f"{self.spec.host}:{self.spec.port}"
            if self.spec.conn_type == "tcp"
            else self.spec.address
        )

    def _setup_server(self) -> None:
        conn_type = self.spec.conn_type
        if conn_type == "tcp":
            return self._setup_tcp_server()
        elif conn_type == "unix":
            return self._setup_unix_server()
        else:
            raise ValueError(f"Unsupported connection type: {conn_type}")

    def _cleanup_connection_specific(self) -> None:
        """Override in subclasses for connection-specific cleanup."""
        pass

    def _setup_tcp_server(self) -> None:
        """Run TCP Invisibles server on NetKit."""
        logger.info("Starting TCP server...")

        # Create service
        calc = ResourceFactory()

        # Server handler: wraps NetKit connection in Invisibles protocol
        def handle_connection(netkit_conn: SyncConnection) -> None:
            logger.info("New connection!")

            # Create Invisibles connection
            config = ConnectionConfig(attrs=AttributeAccessConfig(allow_all_attrs=True))
            config.connection_id = "server"
            codec = MicroPackCodec()

            invisibles_conn = InvisiblesConnection(
                netkit_connection=netkit_conn,
                codec=codec,
                root_service=calc,
                config=config,
            )

            # Keep serving while connection is open
            # This allows the server to handle client requests
            try:
                while netkit_conn.is_connected():
                    invisibles_conn._serve_one(timeout=1.0)
            except Exception as e:
                logger.error(f"Error: {e}")
            finally:
                logger.info("Connection closed")

        # Create NetKit server
        server = SyncServer(
            listener_factory=lambda: TCPListener(),
            framing_factory=lambda t: LengthPrefixedFraming(t, max_frame_size=1024 * 1024),
            executor=ThreadPoolExecutor(max_workers=10),
        )

        server.set_handler(handle_connection)

        self._server = server

    def _setup_unix_server(self) -> None:
        logger.info("Starting...")

        # Server handler: wraps NetKit connection in Invisibles protocol
        def handle_connection(netkit_conn: SyncConnection) -> None:
            logger.info("New connection!")

            # Create Invisibles connection
            config = ConnectionConfig(attrs=AttributeAccessConfig(allow_all_attrs=True))
            config.connection_id = "server"
            codec = MicroPackCodec()

            invisibles_conn = InvisiblesConnection(
                netkit_connection=netkit_conn,
                codec=codec,
                root_service=self.spec.factory_cls(),
                config=config,
            )

            # Keep serving while connection is open
            # This allows the server to handle client requests
            try:
                while netkit_conn.is_connected():
                    invisibles_conn._serve_one(timeout=1.0)
            except Exception as e:
                logger.error(f"Error: {e}")
            finally:
                logger.info("Connection closed")

        # Create NetKit server
        server = SyncServer(
            listener_factory=lambda: UnixSocketListener(),
            framing_factory=lambda t: LengthPrefixedFraming(t, max_frame_size=1024 * 1024),
            executor=ThreadPoolExecutor(max_workers=10),
        )

        server.set_handler(handle_connection)

        self._server = server

    # --- Common server functionality --- #

    def setup(self) -> None:
        """Initialize the Invisibles server.

        Creates the factory and service instance, then configures the server.
        """
        self._server: SyncServer | None = None
        self._ready_event = threading.Event()

        self.factory: ResourceFactory | None = None
        self.factory_cls: type[ResourceFactory] = ResourceFactory

        self._setup_server()

        logger.info(f"Invisibles server configured for {self.endpoint}")

    def cleanup(self) -> None:
        """Clean up the Invisibles server."""
        logger.info("Invisibles server service cleaning up...")
        self.stop()

    def _check_server_listening(self) -> bool:
        """Check if server is actually listening on its socket."""
        if self.spec.conn_type == "tcp":
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(0.1)
                result = sock.connect_ex((self.spec.host, self.spec.port))
                sock.close()
                return result == 0
            except Exception:
                return False
        else:  # unix socket
            try:
                sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                sock.settimeout(0.1)
                sock.connect(self.spec.address)
                sock.close()
                return True
            except Exception:
                return False

    def start(self) -> None:
        """Start the server in a background thread.

        Raises:
            InvisiblesServerError: If server is not configured or start fails
        """
        if self._server is None:
            raise InvisiblesServerError("Server not configured. Call _setup_server() first.")

        server_thread = threading.Thread(
            target=self._server.start,
            args=(self.spec.address or self.spec.host, self.spec.port),
            daemon=True,
            name="Server",
        )
        server_thread.start()

        # Wait for server to actually start listening
        logger.debug("Waiting for server to be ready...")
        start_time = time.time()
        timeout = 5.0

        while time.time() - start_time < timeout:
            if self._check_server_listening():
                self._ready_event.set()
                logger.info(f"Invisibles server started and ready at {self.endpoint}")
                break
            time.sleep(0.05)
        else:
            logger.error(f"Server failed to start listening within {timeout}s at {self.endpoint}")
            raise InvisiblesServerError(
                f"Server failed to start listening within {timeout}s at {self.endpoint}"
            )

        # BLOCK HERE until server thread finishes
        # (which only happens when stop() is called)
        server_thread.join()
        logger.info("Server thread has exited")

    def wait_until_ready(self, timeout: float = 5.0) -> bool:
        """Wait until the server is ready to accept connections.

        Args:
            timeout: Maximum time to wait in seconds

        Returns:
            True if server is ready, False if timeout
        """
        return self._ready_event.wait(timeout=timeout)

    def stop(self) -> None:
        """Stop the server and clean up resources."""
        if self._server:
            logger.info("Stopping Invisibles server...")
            try:
                # Clear ready state
                self._ready_event.clear()

                # Shutdown all resources first
                if self.factory:
                    self.factory.exposed_shutdown_all_resources()

                # Close the server
                self._server.stop()
            except Exception as e:
                logger.error(f"Error stopping server: {e}")
            finally:
                self._server = None

        # Let subclasses handle additional cleanup
        self._cleanup_connection_specific()

        logger.info("Invisibles server stopped")

    @property
    def active(self) -> bool:
        """Check if server is running.

        Returns:
            True if server thread is active
        """
        return self._server is not None and self._ready_event.is_set()


@attrs.define(frozen=True, slots=True, kw_only=True)
class InvisiblesServerSpec(ResourceSpec):
    """Specification for Invisibles RPC server resource."""

    name: str = "invisibles_server"
    factory: type = InvisiblesServer

    factory_cls: type = ResourceFactory

    conn_type: Literal["unix", "tcp"] = "unix"
    address: str = "./invisibles.sock"
    host: str = "localhost"
    port: int = 18812
