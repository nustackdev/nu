# loomistd/rpyc/server.py
"""
RPyC server service for hosting Loomi resources remotely.

This module provides thin server services that leverage Loomi's resource system
with Attach to automatically attach connection services. The server directly
uses the ResourceFactory and provides TCP and Unix socket variants.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from rpyc.utils.server import ThreadedServer

from .._api import ResourceFactory
from ..exceptions import RPyCServerError
from .logger import logger

__all__ = [
    "BaseRPyCServer",
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
