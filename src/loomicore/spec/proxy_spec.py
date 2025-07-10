"""
ProxySpec: Specification for Proxy Resource Access
"""

from __future__ import annotations

from typing import Generic

import attrs

from .spec import Spec, WrappedSpecT, WrapperConfigT, WrapperSpec

__all__ = [
    "ProxySpec",
]


@attrs.define(frozen=True, slots=True, kw_only=True)
class ProxySpec(WrapperSpec, Generic[WrappedSpecT, WrapperConfigT]):
    """
    Specification for proxy resource access.

    ProxySpec enables transparent access to resources through various transport
    mechanisms (RPyC, Ray, HTTP, etc.) with automatic lifecycle management.
    It supports optional server auto-spawning and multi-level proxy wrapping.

    Attributes:
        inner_spec: Specification of the resource to be accessed via proxy
        client_spec: Transport client configuration (required)
        server_spec: Optional transport server configuration for auto-spawning

    Examples:
        Basic proxy specification:
        >>> proxy_spec = ProxySpec(
        ...     inner_spec=ComputeServiceSpec(),
        ...     client_spec=RPyCClientSpec(host="worker1", port=18812)
        ... )

        With server auto-spawn:
        >>> proxy_spec = ProxySpec(
        ...     inner_spec=ComputeServiceSpec(),
        ...     client_spec=RPyCClientSpec(host="localhost", port=18812),
        ...     server_spec=RPyCServerSpec(port=18812)
        ... )

        Multi-level proxy (chaining):
        >>> level1 = ComputeServiceSpec().as_proxy(
        ...     client_spec=RPyCClientSpec(host="worker2")
        ... )
        >>> level2 = level1.as_proxy(
        ...     client_spec=RPyCClientSpec(host="worker1")
        ... )
        # Calls flow: client -> worker1 -> worker2 -> resource

    Notes:
        - inner_spec can be any Spec, including another ProxySpec for chaining
        - client_spec must have a factory that implements TransportClientProtocol
        - server_spec is optional; if provided, server will be auto-spawned
        - Supports the WrapperSpec pattern for utilities like get_inner_spec()
    """

    # Resource to be accessed via proxy
    inner_spec: WrappedSpecT

    # Transport client configuration (required)
    client_spec: WrapperConfigT

    # Launcher configuration for auto-spawning server/host (optional)
    launcher_spec: Spec | None = None
