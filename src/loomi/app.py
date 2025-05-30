from __future__ import annotations

from typing import overload

from ._app import AsyncApp as AsyncAppGeneric
from ._app import SyncApp as SyncAppGeneric
from .interfaces.executor.context import ContextProtocol
from .interfaces.executor.executor import AsyncExecutorProtocol, SyncExecutorProtocol
from .interfaces.executor.operations import (
    AppOperationProtocol,
    BranchOperationProtocol,
    DelayOperationProtocol,
    FunctionOperationProtocol,
    LoopOperationProtocol,
    MapOperationProtocol,
    OperationProtocol,
    ParallelOperationProtocol,
    RetryOperationProtocol,
    SequenceOperationProtocol,
    SubscribeOperationProtocol,
    TimeoutOperationProtocol,
)
from .interfaces.state.tree import AsyncStateProtocol, SyncStateProtocol

__all__ = [
    "app_type_factory",
    "AsyncApp",
    "SyncApp",
    "ContextAsyncState",
    "Context",
    "OperationAsyncState",
    "Operation",
    "AsyncAppGeneric",
    "SyncAppGeneric",
]

# --- Type aliases --- #

ContextAsyncState = ContextProtocol["OperationAsyncState", AsyncStateProtocol]
OperationAsyncState = OperationProtocol["OperationAsyncState", "ContextAsyncState"]

Context = ContextProtocol["Operation", SyncStateProtocol]
Operation = OperationProtocol["Operation", "Context"]

# --- Construct executor types --- #

SyncExecutorSyncState = SyncExecutorProtocol[
    "SyncExecutorSyncState",
    Context,
    OperationProtocol[Operation, Context],
    AppOperationProtocol[Operation, Context],
    BranchOperationProtocol[Operation, Context],
    DelayOperationProtocol[Operation, Context],
    FunctionOperationProtocol[Operation, Context],
    LoopOperationProtocol[Operation, Context],
    MapOperationProtocol[Operation, Context],
    ParallelOperationProtocol[Operation, Context],
    RetryOperationProtocol[Operation, Context],
    SequenceOperationProtocol[Operation, Context],
    SubscribeOperationProtocol[Operation, Context],
    TimeoutOperationProtocol[Operation, Context],
]
AsyncExecutorSyncState = AsyncExecutorProtocol[
    "AsyncExecutorSyncState",
    Context,
    OperationProtocol[Operation, Context],
    AppOperationProtocol[Operation, Context],
    BranchOperationProtocol[Operation, Context],
    DelayOperationProtocol[Operation, Context],
    FunctionOperationProtocol[Operation, Context],
    LoopOperationProtocol[Operation, Context],
    MapOperationProtocol[Operation, Context],
    ParallelOperationProtocol[Operation, Context],
    RetryOperationProtocol[Operation, Context],
    SequenceOperationProtocol[Operation, Context],
    SubscribeOperationProtocol[Operation, Context],
    TimeoutOperationProtocol[Operation, Context],
]
AsyncExecutorAsyncState = AsyncExecutorProtocol[
    "AsyncExecutorAsyncState",
    ContextAsyncState,
    OperationProtocol[OperationAsyncState, ContextAsyncState],
    AppOperationProtocol[OperationAsyncState, ContextAsyncState],
    BranchOperationProtocol[OperationAsyncState, ContextAsyncState],
    DelayOperationProtocol[OperationAsyncState, ContextAsyncState],
    FunctionOperationProtocol[OperationAsyncState, ContextAsyncState],
    LoopOperationProtocol[OperationAsyncState, ContextAsyncState],
    MapOperationProtocol[OperationAsyncState, ContextAsyncState],
    ParallelOperationProtocol[OperationAsyncState, ContextAsyncState],
    RetryOperationProtocol[OperationAsyncState, ContextAsyncState],
    SequenceOperationProtocol[OperationAsyncState, ContextAsyncState],
    SubscribeOperationProtocol[OperationAsyncState, ContextAsyncState],
    TimeoutOperationProtocol[OperationAsyncState, ContextAsyncState],
]

# --- Construct app types --- #


class AsyncApp(AsyncAppGeneric[SyncStateProtocol, AsyncExecutorSyncState]):
    """
    App that implements:
        - async app protocol,
        - async executor protocol,
        - sync state protocol.

    It is used to create asynchronous applications with async execution capabilities and synchronous state management.
    """


class SyncApp(SyncAppGeneric[SyncStateProtocol, SyncExecutorSyncState]):
    """
    App that implements:
        - sync app protocol,
        - sync executor protocol,
        - sync state protocol.

    It is used to create asynchronous applications with synchronous execution capabilities and state management.
    """


class AsyncAppAsyncState(AsyncAppGeneric[AsyncStateProtocol, AsyncExecutorAsyncState]):
    """
    App that implements:
        - async app protocol,
        - async executor protocol,
        - async state protocol.

    It is used to create asynchronous applications with async execution capabilities and async state management (e.g., distributed state env).
    """


@overload
def app_type_factory(
    base_async: bool = True, state_async: bool = True, executor_async: bool = True
) -> type[AsyncAppAsyncState]: ...


@overload
def app_type_factory(
    base_async: bool = False, state_async: bool = False, executor_async: bool = False
) -> type[SyncApp]: ...


@overload
def app_type_factory(
    base_async: bool = True, state_async: bool = False, executor_async: bool = True
) -> type[AsyncApp]: ...


def app_type_factory(
    base_async: bool = True, state_async: bool = True, executor_async: bool = True
) -> type[AsyncApp | SyncApp | AsyncAppAsyncState]:
    """
    Construct a new class that inherits from the provided base class and
    the provided state and executor classes.
    """

    if base_async and state_async and executor_async:
        return AsyncApp
    elif not base_async and not state_async and not executor_async:
        return SyncApp
    elif base_async and not state_async and executor_async:
        return AsyncAppAsyncState
    else:
        raise TypeError("Invalid combination of async and sync types.")
