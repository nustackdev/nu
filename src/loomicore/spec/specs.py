"""
Resource Spec Module

This implements a high-performance, type-safe spec system for Loomi with:
- attrs for frozen structs
- SHA-256 content-based hashing for deterministic keys
- Cached computations for performance
- Fluent transformation API
"""

from __future__ import annotations

from typing import Any, Generic, Type, TypeVar

import attrs

from .base import BaseSpec

__all__ = [
    "Spec",
    "WrapperSpec",
]


WrappedSpecT = TypeVar("WrappedSpecT", bound="Spec")
WrapperConfigT = TypeVar("WrapperConfigT", bound="Spec")


@attrs.define(frozen=True, slots=True, kw_only=True)
class Spec(BaseSpec):
    """
    Specification class for all Loomi specs.
    """

    pass


@attrs.define(frozen=True, slots=True, kw_only=True)
class ResourceSpec(Spec):
    """
    Specification class for all Loomi specs.
    """

    factory: Type[Any]
    name: str = ""


@attrs.define(frozen=True, slots=True, kw_only=True)
class WrapperSpec(Spec):
    """
    Base class for specs that wrap other specs.

    Provides coordinator patterns for distributed resources.
    """

    inner_spec: ResourceSpec


@attrs.define(frozen=True, slots=True, kw_only=True)
class ProxySpec(WrapperSpec, Generic[WrappedSpecT, WrapperConfigT]):
    """
    Specification for proxy resource access.

    ProxySpec enables transparent access to resources through various transport
    mechanisms (RPyC, Ray, HTTP, etc.) with automatic lifecycle management.
    It supports optional server auto-spawning and multi-level proxy wrapping.

    Attributes:
        inner_spec: ResourceSpecification of the resource to be accessed via proxy
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
    launcher_spec: ResourceSpec | None = None
