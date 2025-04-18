from typing import overload

from loomi import AsyncApp as LoomiAsyncApp
from loomi import SyncApp as LoomiSyncApp
from loomi.interfaces.state.state import AsyncStateProtocol
from loomi.interfaces.state.tree import AsyncTreeDictProtocol, SyncTreeDictProtocol

from .aexecutor.engine import ExecutionEngine
from .state import State

__all__ = [
    "app_type_factory",
    "AsyncApp",
]


@overload
def app_type_factory(
    base_async: bool = True, state_async: bool = True, executor_async: bool = True
) -> type[LoomiAsyncApp[State, ExecutionEngine[AsyncStateProtocol, AsyncTreeDictProtocol]]]: ...


@overload
def app_type_factory(
    base_async: bool = False, state_async: bool = False, executor_async: bool = False
) -> type[LoomiSyncApp]: ...


def app_type_factory(
    base_async: bool = True, state_async: bool = True, executor_async: bool = True
) -> type[LoomiAsyncApp | LoomiSyncApp]:
    """
    Construct a new class that inherits from the provided base class and
    the provided state and executor classes.
    """
    if not base_async:
        raise NotImplementedError("SyncApp is not implemented. Please use AsyncApp.")
    else:
        base = LoomiAsyncApp

    if not state_async:
        raise NotImplementedError("SyncState is not implemented. Please use AsyncState.")
    else:
        state = State

    if not executor_async:
        raise NotImplementedError(
            "SyncExecutionEngine is not implemented. Please use AsyncExecutionEngine."
        )
    else:
        executor = ExecutionEngine

    return base[
        state, executor[state, AsyncTreeDictProtocol if state_async else SyncTreeDictProtocol]
    ]


AsyncApp = app_type_factory(True, True, True)
