"""
Transport protocol interfaces for the proxy system.

This module defines minimal protocol interfaces that transport implementations
must conform to. The protocols are intentionally minimal to avoid forcing
transport-specific implementation details while ensuring basic lifecycle
management capabilities.

The protocols form the contract between the core proxy system and transport
implementations (RPyC, Ray, HTTP, etc.), enabling transport-agnostic proxy
coordination while maintaining implementation flexibility.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from loomicore.spec import Spec

__all__ = [
    "TransportClientProtocol",
]


@runtime_checkable
class TransportClientProtocol(Protocol):
    """
    Minimal protocol interface for transport clients.

    Transport clients are responsible for establishing connections to servers
    and providing transport-specific proxy objects for remote resource access.
    This protocol defines only the essential lifecycle and proxy retrieval
    methods, leaving transport-specific communication details to implementations.

    Examples:
        RPyC clients return netref objects (already transparent)
        Ray clients return custom proxy wrappers with __getattr__
        HTTP clients return REST-based proxy objects
    """

    def get_proxy(self, resource_spec: Spec) -> Any:
        """
        Get transport-specific proxy object for the given resource specification.

        This is the core method that returns the actual proxy object that will
        handle method forwarding. The returned object is implementation-specific:
        - RPyC: Returns netref object (transparent)
        - Ray: Returns custom proxy wrapper with __getattr__
        - HTTP: Returns REST client wrapper

        The proxy object should support attribute access and method calls
        that will be forwarded to the remote resource.

        Args:
            resource_spec: ResourceSpecification of the resource to proxy

        Returns:
            Transport-specific proxy object that supports method forwarding

        Raises:
            ConnectionError: If not connected or connection is unhealthy
            ProxyError: If proxy creation fails
            ResourceError: If remote resource cannot be resolved

        Notes:
            - Proxy object lifetime is managed by the coordinator
            - Implementation should handle resource caching/deduplication on server side
            - Proxy should support transparent method calls and attribute access
        """
        ...
