"""
Loomicore Proxy System - Transparent proxy resource access.

This package provides a robust proxy system for transparent access to resources
through various transport mechanisms (RPyC, Ray, HTTP, etc.). The system supports
automatic lifecycle management, transport abstraction, and seamless integration
with Loomi's resource and dependency management patterns.

Key Features:
    - Transport-agnostic proxy coordination
    - Automatic server spawning and lifecycle management
    - Multi-level proxy wrapping support
    - Full integration with Loomi Attach and resource patterns
    - Minimal protocol interfaces for transport flexibility

Components:
    ProxyCoordinator: Main component providing Loomi lifecycle integration
    TransportClientProtocol/TransportServerProtocol: Minimal transport interfaces
    Factory functions: Integration with Loomi resource creation

Usage:
    Direct usage:
    >>> from loomicore.proxy import create_proxy_coordinator
    >>> from loomicore.spec import ProxySpec
    >>>
    >>> spec = ProxySpec(
    ...     inner_spec=ComputeServiceSpec(),
    ...     client_spec=RPyCClientSpec(host="worker1")
    ... )
    >>> with create_proxy_coordinator(spec) as proxy:
    ...     result = proxy.process_item(data)

    With Attach pattern:
    >>> from loomicore.attach import Attach
    >>>
    >>> class DataProcessor(SyncResource):
    ...     compute = Attach(ProxySpec(
    ...         inner_spec=ComputeServiceSpec(),
    ...         client_spec=RPyCClientSpec(host="worker1")
    ...     ))
    ...
    ...     def process_data(self, data):
    ...         return self.compute.process_item(data)

    Multi-level proxy:
    >>> spec = ComputeServiceSpec().as_proxy(
    ...     client_spec=RPyCClientSpec(host="worker2")
    ... ).as_proxy(
    ...     client_spec=RPyCClientSpec(host="worker1")
    ... )
    >>> # Calls flow: client -> worker1 -> worker2 -> resource

Design Principles:
    - Double proxying: ProxyCoordinator handles lifecycle, transport proxy handles calls
    - Minimal protocols: Transport implementations only need essential methods
    - Transport agnostic: Core system works with any transport implementation
    - Transparent integration: Appears as regular Loomi resources to users
    - Multi-level support: Native support for proxy chaining

Transport Implementation:
    Transport implementations provide:
    - TransportClientProtocol: Connection management and proxy retrieval
    - TransportServerProtocol: Server lifecycle management
    - Transport-specific proxy objects: Method forwarding implementation

    The proxy system handles all coordination while transport implementations
    focus on their specific communication patterns and requirements.
"""

# isort: skip_file

from __future__ import annotations

# Core components
from .coordinator import ProxyCoordinator, ProxyCoordinatorSpec
from .proxy_resource import ResourceProxy

# Exceptions
from .exceptions import (
    ProxyConfigurationError,
    ProxyConnectionError,
    ProxyError,
    ProxyLifecycleError,
    ProxyOperationError,
    TransportError,
)

# Protocols for transport implementations
from .transport import TransportClientProtocol

__all__ = [
    # Core components
    "ProxyCoordinator",
    "ResourceProxy",
    # Transport protocols
    "TransportClientProtocol",
    # Exceptions
    "ProxyError",
    "ProxyConfigurationError",
    "ProxyConnectionError",
    "ProxyLifecycleError",
    "ProxyOperationError",
    "TransportError",
]
