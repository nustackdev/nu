"""
Service base class providing dependency injection and component-based architecture.

This module implements the core service functionality with:
- Dependency injection
- Component-based composition
"""

from __future__ import annotations

from loomi.service.base import AsyncService

from .base import ServiceCommonComposer

__all__ = [
    "AsyncServiceComposer",
]


class AsyncServiceComposer(ServiceCommonComposer, AsyncService):
    """
    Service mixin combining dependency injection and component architecture.

    Features:
    - Declarative dependency specification via Attach

    Example:
        class DataService(AsyncService):
            storage = Attach(Storage)
    """

    pass
