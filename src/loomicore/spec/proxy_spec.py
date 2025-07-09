"""
ProxySpec: Specification for Proxy Resource Access
"""

from __future__ import annotations

from typing import Generic, Optional

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

    # Transport server configuration (optional - auto-spawn if provided)
    server_spec: Spec | None = None

    def as_proxy(
        self, client_spec: "WrapperConfigT", server_spec: Optional[Spec] = None
    ) -> "ProxySpec[ProxySpec[WrappedSpecT, WrapperConfigT], WrapperConfigT]":
        """
        Create a new ProxySpec that wraps this specification.

        This method enables multi-level proxy wrapping where resources can be
        accessed through multiple transport layers. Each level adds its own
        transport client/server configuration while preserving the chain.

        Args:
            client_spec: Transport client configuration for the new proxy level
            server_spec: Optional transport server configuration for auto-spawning

        Returns:
            New ProxySpec that wraps this specification

        Examples:
            Single level wrapping:
            >>> base_spec = ComputeServiceSpec()
            >>> proxy_spec = base_spec.as_proxy(
            ...     client_spec=RPyCClientSpec(host="worker1")
            ... )

            Multi-level wrapping:
            >>> base_spec = ComputeServiceSpec()
            >>> level1 = base_spec.as_proxy(
            ...     client_spec=RPyCClientSpec(host="worker2")
            ... )
            >>> level2 = level1.as_proxy(
            ...     client_spec=RPyCClientSpec(host="worker1")
            ... )
            # Creates: client -> worker1 -> worker2 -> resource

            Chaining syntax:
            >>> multi_proxy = ComputeServiceSpec().as_proxy(
            ...     client_spec=RPyCClientSpec(host="worker2")
            ... ).as_proxy(
            ...     client_spec=RPyCClientSpec(host="worker1")
            ... )

        Notes:
            - Each as_proxy() call creates a new layer in the proxy chain
            - Transport protocols handle forwarding through each layer
            - Resource deduplication works based on complete spec chain
            - Method calls flow through all layers transparently
        """
        return ProxySpec(
            inner_spec=self,  # Wrap the current spec (self)
            client_spec=client_spec,
            server_spec=server_spec,
        )
