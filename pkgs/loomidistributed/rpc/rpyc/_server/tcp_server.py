# loomistd/rpyc/server.py
"""
RPyC server service for hosting Loomi resources remotely.

This module provides thin server services that leverage Loomi's resource system
with Attach to automatically attach connection services. The server directly
uses the ResourceFactory and provides TCP and Unix socket variants.
"""

from __future__ import annotations

import attrs
from frozendict import frozendict
from rpyc.utils.server import ThreadedServer

from loomi.service import SyncService
from loomi.spec import ResourceSpec

from .base import BaseRPyCServer
from .logger import logger

__all__ = [
    "RPyCTCPServer",
    "RPyCTCPServerSpec",
]


class RPyCTCPServer(BaseRPyCServer, SyncService):
    """
    TCP-based RPyC server service.

    This service automatically gets a TCP connection injected via Attach
    and configures a TCP-based RPyC server.
    """

    spec: "RPyCTCPServerSpec"

    def _setup_server(self) -> None:
        """Set up TCP-based server."""
        logger.debug(f"Configuring TCP server on {self.spec.bind_address}:{self.spec.bind_port}")

        config = {
            "allow_all_attrs": True,
            "sync_request_timeout": 30,
        }
        config.update(self.spec.config)

        logger.debug(f"RPyC server config: {config}")

        self._server = ThreadedServer(
            service=self.factory_cls,
            hostname=self.spec.bind_address,
            port=self.spec.bind_port,
            auto_register=self.spec.auto_register,
            protocol_config=config,
        )

    @property
    def endpoint(self) -> str:
        """Get string representation of the TCP server endpoint."""
        return f"{self.spec.bind_address}:{self.spec.bind_port}"


@attrs.define(frozen=True, slots=True, kw_only=True)
class RPyCTCPServerSpec(ResourceSpec):
    """Specification for TCP-based RPyC server."""

    name: str = "rpyc_tcp_server"
    factory: type = RPyCTCPServer

    # Server configuration
    bind_address: str = "localhost"
    bind_port: int = 18812
    auto_register: bool = False

    # Connection configuration
    config: frozendict = attrs.field(factory=frozendict)
