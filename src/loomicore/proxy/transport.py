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
    "TransportServerProtocol",
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
            resource_spec: Specification of the resource to proxy

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


@runtime_checkable
class TransportServerProtocol(Protocol):
    """
    Minimal protocol interface for transport servers.

    Transport servers are responsible for hosting resources and serving
    proxy requests from clients. This protocol defines only the essential
    lifecycle methods, leaving transport-specific hosting details to
    implementations.

    Transport servers typically host a resource factory or registry that
    manages resource instances and serves them to connected clients.
    """

    def start(self) -> None:
        """
        Start the transport server and begin accepting connections.

        This method should handle all server startup logic, including:
        - Binding to network interfaces or creating IPC endpoints
        - Starting background threads or event loops
        - Initializing resource factories or registries
        - Setting up any required middleware or handlers

        The method should block until the server is fully ready to accept
        connections, or start the server in background threads and return
        when startup is complete.

        Raises:
            ServerError: If server cannot be started
            ConfigurationError: If server configuration is invalid
            PortInUseError: If network resources are unavailable
        """
        ...

    def stop(self) -> None:
        """
        Stop the transport server and clean up all resources.

        This method should handle graceful server shutdown, including:
        - Stopping acceptance of new connections
        - Completing or terminating active requests
        - Shutting down background threads or event loops
        - Cleaning up hosted resources
        - Releasing network interfaces or IPC endpoints

        The method should be safe to call multiple times and should handle
        cleanup gracefully even if the server encountered errors.

        Notes:
            - Should be safe to call even if server is not running
            - Should complete hosted resource cleanup before returning
            - May be called automatically during resource cleanup
        """
        ...
