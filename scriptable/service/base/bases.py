"""
Base service classes providing asynchronous and synchronous service implementations.

This module defines the foundational service base classes that implement common
functionality for both async and sync service patterns. The classes inherit from
ServiceCommonBase to share core service functionality while implementing their
respective protocols.

Classes:
    ServiceAsyncBase: Base class for asynchronous services
    ServiceSyncBase: Base class for synchronous services
    ServiceBase: Base class for all services (common functionality)
"""

from __future__ import annotations

from scriptable.service.protocols import (
    ServiceAsyncProtocol,
    ServiceCommonProtocol,
    ServiceSyncProtocol,
)

from .common import ServiceCommonBase


class ServiceBase(ServiceCommonBase, ServiceCommonProtocol):
    """
    Base class providing common functionality for all service types.

    This class implements the core features needed by all services, whether
    async or sync. It handles service specifications, identity management,
    registry integration, and basic service properties.
    """

    pass


class ServiceAsyncBase(ServiceBase, ServiceAsyncProtocol):
    """
    Base class for asynchronous services.

    This class combines common service functionality from ServiceCommonBase
    with the async interface defined in ServiceAsyncProtocol. It serves as
    the foundation for all asynchronous service implementations.

    The class inherits core service features like specification management,
    lifecycle tracking, and identity handling while adding the async
    protocol requirements.
    """

    pass


class ServiceSyncBase(ServiceBase, ServiceSyncProtocol):
    """
    Base class for synchronous services.

    This class combines common service functionality from ServiceCommonBase
    with the sync interface defined in ServiceSyncProtocol. It serves as
    the foundation for all synchronous service implementations.

    The class inherits core service features like specification management,
    lifecycle tracking, and identity handling while adding the sync
    protocol requirements.
    """

    pass


__all__ = [
    "ServiceAsyncBase",
    "ServiceSyncBase",
    "ServiceBase",
]
