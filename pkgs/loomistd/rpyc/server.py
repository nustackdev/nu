# loomistd/rpyc/server.py
"""
RPyC server service for hosting Loomi resources remotely.

This module provides thin server services that leverage Loomi's resource system
with UseService to automatically attach connection services. The server directly
uses the ResourceFactory and provides TCP and Unix socket variants.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from rpyc.utils.server import ThreadedServer

from loomi.service import SyncService
from loomi.spec import Spec, SpecField

from .exceptions import RPyCServerError
from .factory import ResourceFactory
from .logger import logger

__all__ = [
    "BaseRPyCServer",
    "RPyCTCPServer",
    "RPyCUnixServer",
    "RPyCTCPServerSpec",
    "RPyCUnixServerSpec",
]


class BaseRPyCServer(ABC):
    """
    Base class for RPyC server services.

    This class provides common server functionality and uses Loomi's service
    architecture. Subclasses implement connection-specific setup.
    """

    # --- Abstract methods and properties to be implemented by subclasses --- #

    @abstractmethod
    def _setup_server(self) -> None:
        """
        Set up the server using connection-specific configuration.

        Subclasses must implement this to create the appropriate server type.
        """
        raise NotImplementedError("Subclasses must implement this method")

    @property
    @abstractmethod
    def endpoint(self) -> str:
        """Get string representation of the server endpoint."""
        raise NotImplementedError("Subclasses must implement this method")

    def _cleanup_connection_specific(self) -> None:
        """Override in subclasses for connection-specific cleanup."""
        pass

    # --- Common server functionality --- #

    def setup(self) -> None:
        """
        Initialize the RPyC server.

        Creates the factory and service instance, then configures the server.
        """
        self._server: ThreadedServer | None = None

        self.factory: ResourceFactory | None = None
        self.factory_cls: type[ResourceFactory] = ResourceFactory

        self._setup_server()

        logger.info(f"RPyC server configured for {self.endpoint}")

    def cleanup(self) -> None:
        """Clean up the RPyC server."""
        logger.info("RPyC server service cleaning up...")
        self.stop()

    def start(self) -> None:
        """
        Start the server in a background thread.

        Raises:
            RPyCServerError: If server is not configured or start fails
        """
        if self._server is None:
            raise RPyCServerError("Server not configured. Call _setup_server() first.")

        if self._server.active:
            logger.warning("RPyC server is already running")
            return

        logger.info("Starting RPyC server...")

        self._server.start()

        logger.info(f"RPyC server started on {self.endpoint}")

    def stop(self) -> None:
        """Stop the server and clean up resources."""
        if self._server:
            logger.info("Stopping RPyC server...")
            try:
                # Shutdown all resources first
                if self.factory:
                    self.factory.exposed_shutdown_all_resources()

                # Close the server
                self._server.close()
            except Exception as e:
                logger.error(f"Error stopping server: {e}")
            finally:
                self._server = None

        # Let subclasses handle additional cleanup
        self._cleanup_connection_specific()

        logger.info("RPyC server stopped")

    @property
    def active(self) -> bool:
        """
        Check if server is running.

        Returns:
            True if server thread is active
        """
        return self._server is not None and self._server.active


class RPyCTCPServer(BaseRPyCServer, SyncService):
    """
    TCP-based RPyC server service.

    This service automatically gets a TCP connection injected via UseService
    and configures a TCP-based RPyC server.
    """

    spec: "RPyCTCPServerSpec"

    def _setup_server(self) -> None:
        """Set up TCP-based server."""
        logger.debug(f"Configuring TCP server on {self.spec.bind_address}:{self.spec.bind_port}")

        self._server = ThreadedServer(
            service=self.factory_cls,
            hostname=self.spec.bind_address,
            port=self.spec.bind_port,
            auto_register=self.spec.auto_register,
            protocol_config={
                "allow_all_attrs": True,
                "sync_request_timeout": 30,
            }.update(self.spec.config),
        )

    @property
    def endpoint(self) -> str:
        """Get string representation of the TCP server endpoint."""
        return f"{self.spec.bind_address}:{self.spec.bind_port}"


class RPyCUnixServer(BaseRPyCServer, SyncService):
    """
    Unix socket-based RPyC server service.

    This service automatically gets a Unix socket connection injected via UseService
    and configures a Unix socket-based RPyC server.
    """

    spec: "RPyCUnixServerSpec"

    def _setup_server(self) -> None:
        """Set up Unix socket-based server."""
        if not self.spec.socket_path:
            raise RPyCServerError("socket_path required for Unix socket server")

        logger.debug(f"Configuring Unix socket server on {self.spec.socket_path}")

        # Remove existing socket file
        socket_file = Path(self.spec.socket_path)
        if socket_file.exists():
            raise RPyCServerError(
                f"Socket file {self.spec.socket_path} already exists. "
                "Please remove it before starting the server."
            )

        # Create Unix socket manually and pass to ThreadedServer
        try:
            self._server = ThreadedServer(
                service=self.factory_cls,
                socket_path=socket_file.resolve(),
                auto_register=self.spec.auto_register,
                protocol_config={
                    "allow_all_attrs": True,
                    "sync_request_timeout": 30,
                }.update(self.spec.config),
            )
        except Exception as e:
            raise RPyCServerError(f"Failed to create Unix socket server: {e}") from e

    def _cleanup_connection_specific(self) -> None:
        """Clean up Unix socket file."""
        if self.spec.socket_path:
            socket_file = Path(self.spec.socket_path)
            if socket_file.exists():
                try:
                    socket_file.unlink()
                except Exception as e:
                    logger.error(f"Error removing socket file: {e}")

    @property
    def endpoint(self) -> str:
        """Get string representation of the Unix socket server endpoint."""
        return self.spec.socket_path


class RPyCTCPServerSpec(Spec):
    """Specification for TCP-based RPyC server."""

    name: str = SpecField(default="rpyc_tcp_server")
    factory: type = SpecField(default=RPyCTCPServer)

    # Server configuration
    bind_address: str = SpecField(default="localhost")
    bind_port: int = SpecField(default=18812)
    auto_register: bool = SpecField(default=False)

    # Connection configuration
    config: dict = SpecField(default_factory=dict)


class RPyCUnixServerSpec(Spec):
    """Specification for Unix socket-based RPyC server."""

    name: str = SpecField(default="rpyc_unix_server")
    factory: type = SpecField(default=RPyCUnixServer)

    # Server configuration
    socket_path: str = SpecField()
    auto_register: bool = SpecField(default=False)

    # Connection configuration
    config: dict = SpecField(default_factory=dict)
