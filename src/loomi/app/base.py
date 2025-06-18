"""
Base app functionality shared between async and sync app types.

The functionality here is inherited by both async and sync service base classes
to ensure consistent behavior across all service types.
"""

from __future__ import annotations

from abc import ABC
from typing import Generic

from loomi._lib.resource import AsyncResource, ResourceABC, Spec, SyncResource

from .types import ExecutorT, StateT, SyncExecutorT, SyncStateT

__all____ = [
    "AppABC",
    "SyncAppABC",
    "AsyncAppABC",
]


class AppABC(ResourceABC, ABC, Generic[StateT, ExecutorT]):
    """
    Base class providing common functionality for all app types.

    This class implements the core features needed by all apps. It handles
    service management, identity management, and basic app properties.

    Class Attributes:
        _services (dict[str, Service]): Dictionary of services used by the app
        _state_service_name (str): Name of the state service

    Properties:
        key (str): Unique app instance identifier
        readable_name (str): Human-readable app identifier
    """

    def __init__(
        self,
        /,
        spec: Spec | None = None,
        *,
        state_spec: Spec | None = None,
        executor_spec: Spec | None = None,
    ) -> None:
        """
        Initialize a new app instance.
        """
        super().__init__(spec=spec)

        self.state_spec = state_spec
        self.executor_spec = executor_spec

        # logger.debug(f"Initialized app '{self.readable_name}'")

    def init_app_deps(self) -> None:
        if self.state_spec is not None:
            self._add_dependency("STATE", spec=self.state_spec)
        if self.executor_spec is not None:
            self._add_dependency("EXECUTOR", spec=self.executor_spec)


class SyncAppABC(AppABC[SyncStateT, SyncExecutorT], SyncResource):
    """
    Base class for synchronous app functionality.
    """

    @property
    def state(self) -> SyncStateT:
        """Check and return app's state service."""
        ...

    @property
    def s(self) -> SyncStateT:
        """Short alias for state adapter."""
        ...

    @property
    def evaluator(self) -> SyncExecutorT:
        """Check and return app's state service."""
        ...

    @property
    def ev(self) -> SyncExecutorT:
        """Short alias for state adapter."""
        ...

    def pre_initialize(self) -> None:
        """
        Pre-initialization hook.

        This method is called before app initialization to set up dependencies.
        """
        super().pre_initialize()
        self.init_app_deps()


class AsyncAppABC(AppABC[StateT, ExecutorT], AsyncResource):
    """
    Base class for asynchronous app functionality.
    """

    @property
    def state(self) -> StateT:
        """Check and return app's state service."""
        ...

    @property
    def s(self) -> StateT:
        """Short alias for state adapter."""
        ...

    @property
    def evaluator(self) -> ExecutorT:
        """Check and return app's state service."""
        ...

    @property
    def ev(self) -> ExecutorT:
        """Short alias for state adapter."""
        ...

    async def pre_initialize(self) -> None:
        """
        Pre-initialization hook.

        This method is called before app initialization to set up dependencies.
        """
        await super().pre_initialize()
        self.init_app_deps()
