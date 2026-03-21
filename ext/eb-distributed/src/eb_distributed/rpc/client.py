"""InvisiblesClient - composables Resource wrapping an Invisibles RPC client.

Connects to an InvisiblesServer and provides transparent proxies
to remote resources via the ResourceFactory.
"""

from __future__ import annotations

import pickle  # nosec: S301
import time

import attrs
from composables import Resource, ResourceSpec
from invisibles import InvisiblesConnection
from invisibles.codec.pickle_codec import PickleCodec
from invisibles.config import AttributeAccessConfig, ConnectionConfig
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

    The remote server hosts a ResourceFactory. get_proxy(spec) calls
    factory.get_resource(spec) to create or retrieve a remote resource.
    """

    spec: InvisiblesClientSpec

    async def setup(self) -> None:
        """Connect to the remote server with retry logic."""
        config = ConnectionConfig(attrs=AttributeAccessConfig(allow_all_attrs=True))
        codec = PickleCodec()

        if self.spec.transport == "unix":
            transport_factory = UnixSocketTransport
        else:
            transport_factory = TCPTransport

        connector = SyncConnector(
            transport_factory=transport_factory,
            framing_factory=lambda t: LengthPrefixedFraming(t, max_frame_size=1024 * 1024),
        )

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
        self._factory = self._connection.sync_request(HANDLE_GET_ROOT)

    async def cleanup(self) -> None:
        """Close the connection."""
        if hasattr(self, "_connection"):
            self._connection.close()

    @property
    def factory(self) -> object:
        """The remote ResourceFactory proxy."""
        return self._factory

    def get_proxy(self, spec: object = None) -> object:
        """Get a proxy to a remote resource by spec.

        Serializes the spec to bytes and calls factory.get_resource(spec_data)
        on the remote server. Specs are frozen data (no lifecycle), so sending
        them by value avoids RPC round trips for attribute access.

        Args:
            spec: ResourceSpec for the resource to create/retrieve

        Returns:
            Transparent proxy to the remote resource
        """
        spec_data = pickle.dumps(spec, protocol=pickle.HIGHEST_PROTOCOL)
        return self._factory.get_resource(spec_data)

    @staticmethod
    def _parse_tcp_address(address: str) -> tuple[str, int]:
        if ":" in address:
            host, port_str = address.rsplit(":", 1)
            return host, int(port_str)
        return "127.0.0.1", int(address)


@attrs.define(frozen=True, slots=True, kw_only=True)
class InvisiblesClientSpec(ResourceSpec):
    """Spec for InvisiblesClient."""

    factory: type = InvisiblesClient
    name: str = "invisibles-client"

    transport: str = "tcp"  # "tcp" or "unix"
    address: str = "127.0.0.1:18812"
    timeout: float = 5.0
    max_retries: int = 3
