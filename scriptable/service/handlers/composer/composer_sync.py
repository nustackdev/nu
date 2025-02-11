"""
Service base class providing dependency injection and component-based architecture.

This module implements the core service functionality with:
- Dependency injection
- Component-based composition
"""

from __future__ import annotations

from scriptable.service.base import ServiceSync

from .base import ServiceCommonComposer


class ServiceComposer(ServiceCommonComposer, ServiceSync):
    """
    Service mixin combining dependency injection and component architecture.

    Features:
    - Declarative dependency specification via Attach

    Example:
        class DataService(SyncService):
            storage = Attach(Storage)
    """

    pass
