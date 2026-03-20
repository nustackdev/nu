"""InvisiblesClient - composables Resource wrapping an Invisibles RPC client.

Connects to an InvisiblesServer and provides a transparent proxy
to the remote root service.
"""

from __future__ import annotations

import time

import attrs
from composables import Resource, ResourceSpec
from invisibles import InvisiblesConnection
from invisibles.codec.pickle_codec import PickleCodec
from invisibles.config import ConnectionConfig
from invisibles.core.consts import HANDLE_GET_ROOT
from invisibles.core.protocol import Protocol
from netkit import SyncConnector
from netkit.framing import LengthPrefixedFraming
from netkit.transports import TCPTransport, UnixSocketTransport


__all__ = [
    "InvisiblesClient",
    "InvisiblesClientSpec",
]


class InvisiblesClient(Resource):
    """Composables Resource that connects to an Invisibles RPC server.

    Provides transparent proxy access to the remote root service.
    """

    spec: InvisiblesClientSpec

    async def setup(self) -> None:
        """Connect to the remote server with retry logic."""
        config = ConnectionConfig()
        codec = PickleCodec()

        if self.spec.transport == "unix":

            def transport_factory() -> UnixSocketTransport:
                return UnixSocketTransport()
        else:

            def transport_factory() -> TCPTransport:
                return TCPTransport()

        connector = SyncConnector(
            transport_factory=transport_factory,
            framing_factory=lambda t: LengthPrefixedFraming(t, max_frame_size=1024 * 1024),
        )

        # Retry connection with backoff
        last_error = None
        for attempt in range(self.spec.max_retries):
            try:
                if self.spec.transport == "unix":
                    netkit_conn = connector.connect(self.spec.address, timeout=self.spec.timeout)
                else:
                    host, port = self._parse_tcp_address(self.spec.address)
                    netkit_conn = connector.connect(host, port, timeout=self.spec.timeout)
                break
            except Exception as e:
                last_error = e
                if attempt < self.spec.max_retries - 1:
                    time.sleep(0.1 * (attempt + 1))
        else:
            raise ConnectionError(
                f"Failed to connect to {self.spec.address} after {self.spec.max_retries} attempts"
            ) from last_error

        protocol = Protocol(codec, config)
        self._connection = InvisiblesConnection(netkit_conn, protocol)
        self._root = self._connection.sync_request(HANDLE_GET_ROOT)

    async def cleanup(self) -> None:
        """Close the connection to the remote server."""
        if hasattr(self, "_connection"):
            self._connection.close()

    @property
    def root(self) -> object:
        """Get the transparent proxy to the remote root service."""
        return self._root

    def get_proxy(self, spec: object = None) -> object:
        """TransportClientProtocol: return the remote proxy."""
        return self._root

    @staticmethod
    def _parse_tcp_address(address: str) -> tuple[str, int]:
        if ":" in address:
            host, port_str = address.rsplit(":", 1)
            return host, int(port_str)
        return "127.0.0.1", int(address)


@attrs.define(frozen=True, slots=True, kw_only=True)
class InvisiblesClientSpec(ResourceSpec):
    """Spec for InvisiblesClient - configures connection parameters."""

    factory: type = InvisiblesClient
    name: str = "invisibles-client"

    transport: str = "tcp"  # "tcp" or "unix"
    address: str = "127.0.0.1:18812"
    timeout: float = 5.0
    max_retries: int = 3
