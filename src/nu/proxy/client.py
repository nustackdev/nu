"""``InvisiblesClient``: connect to an ``InvisiblesServer``.

Exposes its root fabric as a transparent proxy.

FabricLifecycle. On ``asetup`` connects with retry, fetches the remote root
fabric handle, exposes it as ``.root``. On ``acleanup`` closes the
connection.

Pure transport - method calls on ``.root`` go over the wire, sync from the
caller's side (invisibles handles the framing). See ``InvisiblesProxy`` for
the sugar bracket that binds the proxy under a target fabric type in one
step.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from invisibles import BgServingThread, InvisiblesConnection, Protocol
from invisibles.config import AttributeAccessConfig, ConnectionConfig
from invisibles.core.consts import HANDLE_GET_ROOT
from invisibles.netkit import SyncConnector
from invisibles.netkit.framing import LengthPrefixedFraming
from invisibles.netkit.transports import TCPTransport, UnixSocketTransport


if TYPE_CHECKING:
    from nu.lang.runtime import Context


__all__ = ["InvisiblesClient"]


class InvisiblesClient:
    """Connects to an ``InvisiblesServer`` and exposes its root as ``.root``."""

    def __init__(
        self,
        address: str,
        *,
        transport: str = "tcp",
        timeout: float = 5.0,
        max_retries: int = 3,
        bg_serve: bool = False,
        buffered_iteration: bool = True,
    ) -> None:
        if transport not in ("tcp", "unix"):
            msg = f"transport must be 'tcp' or 'unix', got {transport!r}"
            raise ValueError(msg)
        self.address = address
        self.transport = transport
        self.timeout = timeout
        self.max_retries = max_retries
        self.bg_serve = bg_serve
        self.buffered_iteration = buffered_iteration
        self._connection: InvisiblesConnection | None = None
        self._root: object = None
        self._bg: BgServingThread | None = None

    async def asetup(self, ctx: Context) -> None:  # noqa: D102
        config = ConnectionConfig(
            attrs=AttributeAccessConfig(allow_all_attrs=True),
            buffered_iteration=self.buffered_iteration,
        )
        transport_factory = UnixSocketTransport if self.transport == "unix" else TCPTransport
        connector = SyncConnector(
            transport_factory=transport_factory,
            framing_factory=lambda t: LengthPrefixedFraming(t, max_frame_size=1024 * 1024),
        )

        last_error: BaseException | None = None
        netkit_conn = None
        for attempt in range(self.max_retries):
            try:
                if self.transport == "unix":
                    netkit_conn = connector.connect(self.address, timeout=self.timeout)
                else:
                    host, port = self._parse_tcp_address(self.address)
                    netkit_conn = connector.connect(host, port, timeout=self.timeout)
                break
            except Exception as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    time.sleep(0.1 * (attempt + 1))
        if netkit_conn is None:
            msg = f"failed to connect to {self.address} after {self.max_retries} attempts"
            raise ConnectionError(msg) from last_error

        protocol = Protocol(config)
        self._connection = InvisiblesConnection(netkit_conn, protocol)
        self._root = self._connection.sync_request(HANDLE_GET_ROOT)
        if self.bg_serve:
            self._bg = BgServingThread(self._connection)

    async def acleanup(self) -> None:  # noqa: D102
        if self._bg is not None:
            self._bg.stop()
            self._bg = None
        if self._connection is not None:
            self._connection.close()
            self._connection = None
        self._root = None

    @property
    def root(self) -> object:
        """The remote root fabric, as a transparent proxy."""
        return self._root

    @staticmethod
    def _parse_tcp_address(address: str) -> tuple[str, int]:
        if ":" in address:
            host, port_str = address.rsplit(":", 1)
            return host, int(port_str)
        return "127.0.0.1", int(address)
