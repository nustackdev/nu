"""
Service base class providing dependency injection, lifecycle management,
and component-based architecture.

This module implements the core service functionality with:
- Dependency injection and lifecycle (from Memory)
- Component-based composition
- State and operation platforms
- Extension points
"""

from __future__ import annotations

from scriptable.service.base import ServiceAsyncBase

from .base import ServiceCommonComposer


class ServiceComposer(ServiceCommonComposer, ServiceAsyncBase):
    """
    Service mixin combining dependency injection and component architecture.

    Features:
    - Declarative dependency specification via Attach

    Example:
        class DataService(
            Service(
                as_state(RedisStorage),
                as_platform(AsyncPlatform)
            )
        ):
            storage = ServiceSpec(
                protocol=StorageProtocol,
                default_factory=DiskStorage,
                spec_key="storage_spec",
            )
    """

    async def pre_initialize(self):
        await super().pre_initialize()
        self._init_attach()
