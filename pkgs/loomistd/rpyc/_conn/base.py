# loomistd/rpyc/_base.py
"""
Base RPyC connection functionality shared between connection types.

This module provides the common foundation for all RPyC connection types through
the BaseRPyCConnection class. It implements core RPyC features including:
- Connection lifecycle management
- Remote resource resolution
- Configuration handling
- Error management

The functionality here is inherited by both TCP and Unix socket connection classes
to ensure consistent behavior across all connection types.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import final

from rpyc.core import Connection as RPyCConnection

from loomi.spec import Spec, SpecField

from ..exceptions import RPyCConnectionError
from ..types import RPyCConfig
from .logger import logger

__all__ = [
    "BaseRPyCConnection",
    "BaseRPyCConnectionSpec",
]


class BaseRPyCConnection(ABC):
    """
    Base class providing common functionality for all RPyC connection types.

    This class implements the core features needed by all RPyC connections, whether
    TCP or Unix socket based. It handles connection management, resource resolution,
    and basic RPyC operations.

    Attributes:
        config (RPyCConfig): RPyC configuration settings
        auto_connect (bool): Whether to connect automatically during setup

    Properties:
        endpoint (str): String representation of connection endpoint
        is_connected (bool): Connection status
    """

    spec: BaseRPyCConnectionSpec

    # --- Abstract methods and properties to be implemented by subclasses --- #

    @property
    @abstractmethod
    def endpoint(self) -> str:
        """
        Get string representation of the connection endpoint.

        Returns:
            Human-readable endpoint description
        """
        raise NotImplementedError("Subclasses must implement endpoint property")

    @abstractmethod
    def _create_connection_impl(self) -> RPyCConnection:
        """
        Create the specific RPyC connection type.

        Subclasses must implement this method to create the appropriate
        connection type (TCP, Unix socket, etc.).

        Returns:
            RPyC connection instance

        Raises:
            RPyCConnectionError: If connection cannot be created
        """
        raise NotImplementedError("Subclasses must implement this method")

    # --- Instance properties --- #

    @final
    @property
    def is_connected(self) -> bool:
        """
        Check if connected to RPyC server.

        Returns:
            True if connection is active and healthy
        """
        return self._connected and self._connection is not None and not self._connection.closed

    @final
    @property
    def get_connection(self) -> RPyCConnection:
        """
        Get the underlying RPyC connection for direct use.

        Returns:
            RPyC connection instance

        Raises:
            RPyCConnectionError: If not connected
        """
        self._ensure_connected()
        return self._connection

    # --- Lifecycle methods --- #

    def setup(self) -> None:
        """
        Initialize the RPyC connection service.

        Sets up internal state and optionally establishes connection
        based on auto_connect setting.
        """
        self._connection: RPyCConnection
        self._connected = False

        self.connect()

    def cleanup(self) -> None:
        """
        Clean up the RPyC connection service.

        Ensures connection is properly closed and resources are freed.
        """
        if self.is_connected:
            self.disconnect()

    def _ensure_connected(self) -> None:
        """Verify connection state."""
        if not self._connected:
            raise RPyCConnectionError("RPyC connection is not established")

    def _get_rpyc_config(self) -> RPyCConfig:
        """Get RPyC configuration with sensible defaults."""
        default_config: RPyCConfig = {
            "allow_public_attrs": True,
            "sync_request_timeout": 30,
        }
        default_config.update(self.spec.config)

        logger.debug(f"RPyC connection config: {default_config}")

        return default_config

    @final
    def connect(self) -> None:
        """
        Establish connection to RPyC server.

        Creates the connection using the implementation-specific method
        and handles common setup tasks.

        Raises:
            RPyCConnectionError: If connection fails
        """
        if self.is_connected:
            return  # Already connected

        try:
            self._connection = self._create_connection_impl()
            self._connected = True
            logger.debug(f"RPyC connection established to {self.endpoint}")
        except Exception as e:
            logger.debug(f"Failed to connect to {self.endpoint}: {e}")
            raise RPyCConnectionError(f"Failed to connect to {self.endpoint}") from e

    @final
    def disconnect(self) -> None:
        """
        Close connection to RPyC server.

        Properly closes the connection and cleans up resources.
        """
        if self._connection and not self._connection.closed:
            try:
                self._connection.close()
                logger.debug(f"Disconnected from {self.endpoint}")
            except Exception as e:
                logger.debug(f"Error during disconnect from {self.endpoint}: {e}")
            finally:
                self._connected = False


class BaseRPyCConnectionSpec(Spec):
    config: dict = SpecField(default_factory=RPyCConfig)
