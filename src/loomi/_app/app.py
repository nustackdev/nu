from __future__ import annotations

from .composer import AsyncAppComposer, SyncAppComposer
from .handlers.execution_handler import AsyncAppExecutionHandler, SyncAppExecutionHandler
from .handlers.service_handler import AsyncAppServicesHandler, SyncAppServicesHandler
from .handlers.state_handler import AsyncCommonAppStateHandler, SyncCommonAppStateHandler
from .initializer import AsyncAppInitializer, SyncAppInitializer
from .meta import AppMeta
from .types import ExecutorT, StateT, SyncExecutorT, SyncStateT

__all__ = [
    "AsyncApp",
    "SyncApp",
]


class AsyncApp(
    AsyncAppInitializer[StateT, ExecutorT],
    AsyncCommonAppStateHandler[StateT, ExecutorT],
    AsyncAppExecutionHandler[StateT, ExecutorT],
    AsyncAppServicesHandler[StateT, ExecutorT],
    AsyncAppComposer[StateT, ExecutorT],
    metaclass=AppMeta,
):
    pass


class SyncApp(
    SyncAppInitializer[SyncStateT, SyncExecutorT],
    SyncCommonAppStateHandler[SyncStateT, SyncExecutorT],
    SyncAppExecutionHandler[SyncStateT, SyncExecutorT],
    SyncAppServicesHandler[SyncStateT, SyncExecutorT],
    SyncAppComposer[SyncStateT, SyncExecutorT],
    metaclass=AppMeta,
):
    pass
