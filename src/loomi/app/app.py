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

from .execution_handler import AsyncAppExecutionHandler, SyncAppExecutionHandler
from .state_handler import AsyncAppStateHandler, SyncAppStateHandler
from .types import ExecutorT, StateT, SyncExecutorT, SyncStateT

__all__ = [
    "AsyncApp",
    "SyncApp",
]


class AsyncApp(
    AsyncAppStateHandler[StateT, ExecutorT],
    AsyncAppExecutionHandler[StateT, ExecutorT],
):
    pass


class SyncApp(
    SyncAppStateHandler[SyncStateT, SyncExecutorT],
    SyncAppExecutionHandler[SyncStateT, SyncExecutorT],
):
    pass
