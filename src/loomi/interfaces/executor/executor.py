from __future__ import annotations

from typing import Callable, Concatenate, ParamSpec, Protocol, runtime_checkable

from .type_vars import (
    AppOperationT,
    AsyncExecutorT_co,
    BranchOperationT,
    ContextT_contra,
    DelayOperationT,
    FunctionOperationT,
    LoopOperationT,
    MapOperationT,
    OperationT,
    ParallelOperationT,
    RetryOperationT,
    SequenceOperationT,
    SubscribeOperationT,
    SyncContextT_contra,
    SyncExecutorT_co,
    TimeoutOperationT,
)

P = ParamSpec("P")


@runtime_checkable
class AsyncExecutorProtocol(
    Protocol[
        AsyncExecutorT_co,
        ContextT_contra,
        OperationT,
        AppOperationT,
        BranchOperationT,
        DelayOperationT,
        FunctionOperationT,
        LoopOperationT,
        MapOperationT,
        ParallelOperationT,
        RetryOperationT,
        SequenceOperationT,
        SubscribeOperationT,
        TimeoutOperationT,
    ]
):
    """
    Protocol defining the async interface for the execution engine.

    The execution engine is responsible for executing operations and
    providing them with context and services.
    """

    # --- Operations --- #

    Function: type[FunctionOperationT]
    App: type[AppOperationT]
    Branch: type[BranchOperationT]
    Delay: type[DelayOperationT]
    Loop: type[LoopOperationT]
    Map: type[MapOperationT]
    Parallel: type[ParallelOperationT]
    Retry: type[RetryOperationT]
    Sequence: type[SequenceOperationT]
    Subscribe: type[SubscribeOperationT]
    Timeout: type[TimeoutOperationT]

    def Compound(
        self,
        op: Callable[Concatenate[AsyncExecutorT_co, P], OperationT],
    ) -> Callable[P, OperationT]: ...

    # --- Methods --- #

    async def execute(
        self,
        operation: OperationT,
        parent_context: ContextT_contra | None = None,
    ) -> None: ...

    async def exec_operation(
        self,
        context: ContextT_contra,
    ) -> None: ...

    # Atomic operations
    async def exec_function(
        self,
        operation: FunctionOperationT,
        context: ContextT_contra,
    ) -> None: ...

    async def exec_app(
        self,
        operation: AppOperationT,
        context: ContextT_contra,
    ) -> None: ...

    # Flow control operations
    async def exec_sequence(
        self,
        operation: SequenceOperationT,
        context: ContextT_contra,
    ) -> None: ...

    async def exec_parallel(
        self,
        operation: ParallelOperationT,
        context: ContextT_contra,
    ) -> None: ...

    async def exec_branch(
        self,
        operation: BranchOperationT,
        context: ContextT_contra,
    ) -> None: ...

    async def exec_loop(
        self,
        operation: LoopOperationT,
        context: ContextT_contra,
    ) -> None: ...

    # Timing operations
    async def exec_delay(
        self,
        operation: DelayOperationT,
        context: ContextT_contra,
    ) -> None: ...

    async def exec_timeout(
        self,
        operation: TimeoutOperationT,
        context: ContextT_contra,
    ) -> None: ...

    async def exec_retry(
        self,
        operation: RetryOperationT,
        context: ContextT_contra,
    ) -> None: ...

    # Collection operations
    async def exec_map(
        self,
        operation: MapOperationT,
        context: ContextT_contra,
    ) -> None: ...

    # Reactive operations
    async def exec_subscribe(
        self,
        operation: SubscribeOperationT,
        context: ContextT_contra,
    ) -> None: ...


@runtime_checkable
class SyncExecutorProtocol(
    Protocol[
        SyncExecutorT_co,
        SyncContextT_contra,
        OperationT,
        AppOperationT,
        BranchOperationT,
        DelayOperationT,
        FunctionOperationT,
        LoopOperationT,
        MapOperationT,
        ParallelOperationT,
        RetryOperationT,
        SequenceOperationT,
        SubscribeOperationT,
        TimeoutOperationT,
    ]
):
    """
    Protocol defining the sync interface for the execution engine.

    The execution engine is responsible for executing operations and
    providing them with context and services.
    """

    # --- Operations --- #

    Function: type[FunctionOperationT]
    App: type[AppOperationT]
    Branch: type[BranchOperationT]
    Delay: type[DelayOperationT]
    Loop: type[LoopOperationT]
    Map: type[MapOperationT]
    Parallel: type[ParallelOperationT]
    Retry: type[RetryOperationT]
    Sequence: type[SequenceOperationT]
    Subscribe: type[SubscribeOperationT]
    Timeout: type[TimeoutOperationT]

    def Compound(
        self,
        compound_op: Callable[Concatenate[SyncExecutorT_co, P], OperationT],
    ) -> Callable[P, OperationT]: ...

    # --- Methods --- #

    def execute(
        self,
        operation: OperationT,
        parent_context: SyncContextT_contra | None = None,
    ) -> None: ...

    def exec_operation(
        self,
        context: SyncContextT_contra,
    ) -> None: ...

    # Atomic operations
    def exec_function(
        self,
        operation: FunctionOperationT,
        context: SyncContextT_contra,
    ) -> None: ...

    def exec_app(
        self,
        operation: AppOperationT,
        context: SyncContextT_contra,
    ) -> None: ...

    # Flow control operations
    def exec_sequence(
        self,
        operation: SequenceOperationT,
        context: SyncContextT_contra,
    ) -> None: ...

    def exec_parallel(
        self,
        operation: ParallelOperationT,
        context: SyncContextT_contra,
    ) -> None: ...

    def exec_branch(
        self,
        operation: BranchOperationT,
        context: SyncContextT_contra,
    ) -> None: ...

    def exec_loop(
        self,
        operation: LoopOperationT,
        context: SyncContextT_contra,
    ) -> None: ...

    # Timing operations
    def exec_delay(
        self,
        operation: DelayOperationT,
        context: SyncContextT_contra,
    ) -> None: ...

    def exec_timeout(
        self,
        operation: TimeoutOperationT,
        context: SyncContextT_contra,
    ) -> None: ...

    def exec_retry(
        self,
        operation: RetryOperationT,
        context: SyncContextT_contra,
    ) -> None: ...

    # Collection operations
    def exec_map(
        self,
        operation: MapOperationT,
        context: SyncContextT_contra,
    ) -> None: ...

    # Reactive operations
    def exec_subscribe(
        self,
        operation: SubscribeOperationT,
        context: SyncContextT_contra,
    ) -> None: ...
