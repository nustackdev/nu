# loomistd/rpyc/server.py
"""
RPyC server service for hosting Loomi resources remotely.

This module provides thin server services that leverage Loomi's resource system
with Attach to automatically attach connection services. The server directly
uses the ResourceFactory and provides TCP and Unix socket variants.
"""

from __future__ import annotations

from pathlib import Path

import attrs
from frozendict import frozendict
from rpyc.utils.server import ThreadedServer

from loomi import ResourceSpec, SyncService

from ..exceptions import RPyCServerError
from .base import BaseRPyCServer
from .logger import logger

__all__ = [
    "RPyCUnixServer",
    "RPyCUnixServerSpec",
]


class RPyCUnixServer(BaseRPyCServer, SyncService):
    """
    Unix socket-based RPyC server service.

    This service automatically gets a Unix socket connection injected via Attach
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

        config = {
            "allow_all_attrs": True,
            "sync_request_timeout": 300,  # TODO: hardcoded 5 minutes. move to config
        }
        config.update(self.spec.config)

        logger.debug(f"RPyC server config: {config}")

        # Create Unix socket manually and pass to ThreadedServer
        try:
            self._server = ThreadedServer(
                service=self.factory_cls,
                socket_path=str(socket_file.resolve()),
                auto_register=self.spec.auto_register,
                protocol_config=config,
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


@attrs.define(frozen=True, slots=True, kw_only=True)
class RPyCUnixServerSpec(ResourceSpec):
    """Specification for Unix socket-based RPyC server."""

    name: str = "rpyc_unix_server"
    factory: type = RPyCUnixServer

    # Server configuration
    socket_path: str = "/tmp/loomi_rpyc.sock"
    auto_register: bool = False

    # Connection configuration
    config: frozendict = attrs.field(factory=frozendict)
