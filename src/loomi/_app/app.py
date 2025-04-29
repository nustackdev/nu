"""
Apps for synchronous and asynchronous functionality.

Apps are constructed by composing various components, including initialization,
execution handling, service handling, and state management.
The `AsyncApp` class is designed for asynchronous applications, while the `SyncApp` class
is designed for synchronous applications.

The `AsyncApp` class inherits from:
- `AsyncAppInitializer`: Handles asynchronous app initialization.
- `AsyncCommonAppStateHandler`: Manages the app's state asynchronously.
- `AsyncAppExecutionHandler`: Handles asynchronous execution of app functions.
- `AsyncAppServicesHandler`: Manages asynchronous service handling.

The `SyncApp` class inherits from:
- `SyncAppInitializer`: Handles synchronous app initialization.
- `SyncCommonAppStateHandler`: Manages the app's state synchronously.
- `SyncAppExecutionHandler`: Handles synchronous execution of app functions.
- `SyncAppServicesHandler`: Manages synchronous service handling.
"""

from __future__ import annotations

from .composer import AsyncAppComposer, SyncAppComposer
from .handlers.execution_handler import AsyncAppExecutionHandler, SyncAppExecutionHandler
from .handlers.service_handler import AsyncAppServicesHandler, SyncAppServicesHandler
from .handlers.state_handler import AsyncCommonAppStateHandler, SyncCommonAppStateHandler
from .initializer import AsyncAppInitializer, SyncAppInitializer
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
):
    pass


class SyncApp(
    SyncAppInitializer[SyncStateT, SyncExecutorT],
    SyncCommonAppStateHandler[SyncStateT, SyncExecutorT],
    SyncAppExecutionHandler[SyncStateT, SyncExecutorT],
    SyncAppServicesHandler[SyncStateT, SyncExecutorT],
    SyncAppComposer[SyncStateT, SyncExecutorT],
):
    pass
