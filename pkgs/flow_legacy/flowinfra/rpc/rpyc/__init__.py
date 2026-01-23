# everyflowstd/rpyc/__init__.py
"""EveryFlowstD RPyC Package - Dedicated RPyC implementation for EveryFlow remote resources.

This package provides RPyC-specific services for remote resource connectivity.
It embraces RPyC's features and wraps them in EveryFlow's service architecture.

Components:
- Connection subpackage: TCP and Unix socket connections (for clients)
- Server: Thin RPyC server services (TCP and Unix variants)
- Client: RPyC client services (TCP and Unix variants)
"""

from __future__ import annotations

# Core components
from ._client import (
    RPyCClient,
    RPyCTCPClientSpec,
    RPyCTCPConnection,
    RPyCTCPConnectionSpec,
    RPyCUnixClientSpec,
    RPyCUnixConnection,
    RPyCUnixConnectionSpec,
)
from ._server import (
    BaseRPyCServer,
    RPyCTCPServer,
    RPyCTCPServerSpec,
    RPyCUnixServer,
    RPyCUnixServerSpec,
)


__all__ = [
    # Connection types (used by clients)
    "RPyCTCPConnection",
    "RPyCUnixConnection",
    "RPyCTCPConnectionSpec",
    "RPyCUnixConnectionSpec",
    # Core services
    "BaseRPyCServer",
    "RPyCTCPServer",
    "RPyCUnixServer",
    "RPyCClient",
    # Specifications
    "RPyCTCPServerSpec",
    "RPyCUnixServerSpec",
    "RPyCTCPClientSpec",
    "RPyCUnixClientSpec",
]
