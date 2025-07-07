from __future__ import annotations

import attrs

from loomi.spec import Spec
from loomistd.remote import RPyCTCPServer, RPyCUnixServer


@attrs.define(frozen=True, slots=True, kw_only=True)
class WorkerTCPServerSpec(Spec):
    """Specification for TCP-based RPyC server."""

    name: str = "rpyc_tcp_server"
    factory: type = RPyCTCPServer

    # Server configuration
    bind_address: str = "localhost"
    bind_start_port: int = 18812
    auto_register: bool = False

    # Connection configuration
    config: dict = attrs.field(factory=dict)


@attrs.define(frozen=True, slots=True, kw_only=True)
class WorkerUnixServerSpec(Spec):
    """Specification for Unix socket-based RPyC server."""

    name: str = "rpyc_unix_server"
    factory: type = RPyCUnixServer

    # Server configuration
    socket_path: str = "/tmp/loomi_rpyc.sock"
    auto_register: bool = False

    # Connection configuration
    config: dict = attrs.field(factory=dict)
