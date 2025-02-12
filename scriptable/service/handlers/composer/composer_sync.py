"""
Service base class providing dependency injection and component-based architecture.

This module implements the core service functionality with:
- Dependency injection
- Component-based composition
"""

from __future__ import annotations

from scriptable.service.base import SyncService

from .base import ServiceCommonComposer

__all__ = [
    "SyncServiceComposer",
]


class SyncServiceComposer(ServiceCommonComposer, SyncService):
    """
    Service mixin combining dependency injection and component architecture.

    Features:
    - Declarative dependency specification via Attach

    Example:
        class DataService(SyncService):
            storage = Attach(Storage)
    """

    pass
