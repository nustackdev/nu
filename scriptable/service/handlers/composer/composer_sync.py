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

from scriptable.service.base import ServiceSyncBase

from .base import ServiceCommonComposer


class ServiceComposer(ServiceCommonComposer, ServiceSyncBase):
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

    def pre_initialize(self):
        super().pre_initialize()
        self._init_attach()
