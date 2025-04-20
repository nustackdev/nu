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
from .interfaces.state.state import AsyncStateProtocol, SyncStateProtocol
from .interfaces.state.tree import AsyncTreeDictProtocol, SyncTreeDictProtocol
from .interfaces.state.types import StateValue

__all__ = [
    "app_type_factory",
    "AsyncApp",
    "SyncApp",
    "AsyncContext",
    "SyncContext",
    "AsyncOperation",
    "SyncOperation",
    "AsyncAppGeneric",
    "SyncAppGeneric",
]

# --- Type aliases --- #

AsyncContext = ContextProtocol["AsyncOperation", AsyncTreeDictProtocol[StateValue]]
AsyncOperation = OperationProtocol[OperationProtocol, "AsyncContext"]
SyncContext = ContextProtocol["SyncOperation", SyncTreeDictProtocol[StateValue]]
SyncOperation = OperationProtocol[OperationProtocol, "SyncContext"]

# --- Construct app types --- #


class AsyncApp(
    AsyncAppGeneric[
        AsyncStateProtocol[StateValue],
        AsyncExecutorProtocol[
            AsyncContext,
            OperationProtocol[AsyncOperation, AsyncContext],
            AppOperationProtocol[AsyncOperation, AsyncContext],
            BranchOperationProtocol[AsyncOperation, AsyncContext],
            DelayOperationProtocol[AsyncOperation, AsyncContext],
            FunctionOperationProtocol[AsyncOperation, AsyncContext],
            LoopOperationProtocol[AsyncOperation, AsyncContext],
            MapOperationProtocol[AsyncOperation, AsyncContext],
            ParallelOperationProtocol[AsyncOperation, AsyncContext],
            RetryOperationProtocol[AsyncOperation, AsyncContext],
            SequenceOperationProtocol[AsyncOperation, AsyncContext],
            SubscribeOperationProtocol[AsyncOperation, AsyncContext],
            TimeoutOperationProtocol[AsyncOperation, AsyncContext],
        ],
    ]
):
    """
    App that implements the AsyncStateProtocol and AsyncExecutorProtocol interfaces.
    It is used to create asynchronous applications with state management and
    execution capabilities.

    Future handlers are going to also follow asynchronous patterns.
    """


class SyncApp(
    SyncAppGeneric[
        SyncStateProtocol[StateValue],
        SyncExecutorProtocol[
            SyncContext,
            OperationProtocol[SyncOperation, SyncContext],
            AppOperationProtocol[SyncOperation, SyncContext],
            BranchOperationProtocol[SyncOperation, SyncContext],
            DelayOperationProtocol[SyncOperation, SyncContext],
            FunctionOperationProtocol[SyncOperation, SyncContext],
            LoopOperationProtocol[SyncOperation, SyncContext],
            MapOperationProtocol[SyncOperation, SyncContext],
            ParallelOperationProtocol[SyncOperation, SyncContext],
            RetryOperationProtocol[SyncOperation, SyncContext],
            SequenceOperationProtocol[SyncOperation, SyncContext],
            SubscribeOperationProtocol[SyncOperation, SyncContext],
            TimeoutOperationProtocol[SyncOperation, SyncContext],
        ],
    ]
):
    """
    App that implements the SyncStateProtocol and SyncExecutorProtocol interfaces.
    It is used to create synchronous applications with state management and
    execution capabilities.

    Future handlers are going to also follow synchronous patterns.
    """


class AsyncAppSSAE(
    AsyncAppGeneric[
        SyncStateProtocol[StateValue],
        AsyncExecutorProtocol[
            SyncContext,
            OperationProtocol[SyncOperation, SyncContext],
            AppOperationProtocol[SyncOperation, SyncContext],
            BranchOperationProtocol[SyncOperation, SyncContext],
            DelayOperationProtocol[SyncOperation, SyncContext],
            FunctionOperationProtocol[SyncOperation, SyncContext],
            LoopOperationProtocol[SyncOperation, SyncContext],
            MapOperationProtocol[SyncOperation, SyncContext],
            ParallelOperationProtocol[SyncOperation, SyncContext],
            RetryOperationProtocol[SyncOperation, SyncContext],
            SequenceOperationProtocol[SyncOperation, SyncContext],
            SubscribeOperationProtocol[SyncOperation, SyncContext],
            TimeoutOperationProtocol[SyncOperation, SyncContext],
        ],
    ]
):
    """
    App that implements the SyncStateProtocol and AsyncExecutorProtocol interfaces.
    It is used to create asynchronous applications with synchronous state management
    and execution capabilities.
    """


@overload
def app_type_factory(
    base_async: bool = True, state_async: bool = True, executor_async: bool = True
) -> type[AsyncApp]: ...


@overload
def app_type_factory(
    base_async: bool = False, state_async: bool = False, executor_async: bool = False
) -> type[SyncApp]: ...


@overload
def app_type_factory(
    base_async: bool = True, state_async: bool = False, executor_async: bool = True
) -> type[AsyncAppSSAE]: ...


def app_type_factory(
    base_async: bool = True, state_async: bool = True, executor_async: bool = True
) -> type[AsyncApp | SyncApp | AsyncAppSSAE]:
    """
    Construct a new class that inherits from the provided base class and
    the provided state and executor classes.
    """

    if base_async and state_async and executor_async:
        return AsyncApp
    elif not base_async and not state_async and not executor_async:
        return SyncApp
    elif base_async and not state_async and executor_async:
        return AsyncAppSSAE
    else:
        raise TypeError("Invalid combination of async and sync types.")
