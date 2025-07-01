from __future__ import annotations

from loomi.spec import Spec, SpecField
from loomistd.remote import RPyCTCPServer, RPyCUnixServer


class WorkerTCPServerSpec(Spec):
    """Specification for TCP-based RPyC server."""

    name: str = SpecField(default="rpyc_tcp_server")
    factory: type = SpecField(default=RPyCTCPServer)

    # Server configuration
    bind_address: str = SpecField(default="localhost")
    bind_start_port: int = SpecField(default=18812)
    auto_register: bool = SpecField(default=False)

    # Connection configuration
    config: dict = SpecField(default_factory=dict)


class WorkerUnixServerSpec(Spec):
    """Specification for Unix socket-based RPyC server."""

    name: str = SpecField(default="rpyc_unix_server")
    factory: type = SpecField(default=RPyCUnixServer)

    # Server configuration
    socket_path: str = SpecField(default="/tmp/loomi_rpyc.sock")
    auto_register: bool = SpecField(default=False)

    # Connection configuration
    config: dict = SpecField(default_factory=dict)
