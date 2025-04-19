from __future__ import annotations

from typing import Protocol, runtime_checkable

from .type_vars import (
    AppOperationT_contra,
    BranchOperationT_contra,
    ContextT_contra,
    DelayOperationT_contra,
    FunctionOperationT_contra,
    LoopOperationT_contra,
    MapOperationT_contra,
    OperationT_contra,
    ParallelOperationT_contra,
    RetryOperationT_contra,
    SequenceOperationT_contra,
    SubscribeOperationT_contra,
    SyncContextT_contra,
    TimeoutOperationT_contra,
)


@runtime_checkable
class AsyncExecutorProtocol(
    Protocol[
        ContextT_contra,
        OperationT_contra,
        AppOperationT_contra,
        BranchOperationT_contra,
        DelayOperationT_contra,
        FunctionOperationT_contra,
        LoopOperationT_contra,
        MapOperationT_contra,
        ParallelOperationT_contra,
        RetryOperationT_contra,
        SequenceOperationT_contra,
        SubscribeOperationT_contra,
        TimeoutOperationT_contra,
    ]
):
    """
    Protocol defining the async interface for the execution engine.

    The execution engine is responsible for executing operations and
    providing them with context and services.
    """

    async def execute(
        self,
        operation: OperationT_contra,
        parent_context: ContextT_contra | None = None,
    ) -> None: ...

    async def exec_operation(
        self,
        context: ContextT_contra,
    ) -> None: ...

    # Atomic operations
    async def exec_function(
        self,
        operation: FunctionOperationT_contra,
        context: ContextT_contra,
    ) -> None: ...

    async def exec_app(
        self,
        operation: AppOperationT_contra,
        context: ContextT_contra,
    ) -> None: ...

    # Flow control operations
    async def exec_sequence(
        self,
        operation: SequenceOperationT_contra,
        context: ContextT_contra,
    ) -> None: ...

    async def exec_parallel(
        self,
        operation: ParallelOperationT_contra,
        context: ContextT_contra,
    ) -> None: ...

    async def exec_branch(
        self,
        operation: BranchOperationT_contra,
        context: ContextT_contra,
    ) -> None: ...

    async def exec_loop(
        self,
        operation: LoopOperationT_contra,
        context: ContextT_contra,
    ) -> None: ...

    # Timing operations
    async def exec_delay(
        self,
        operation: DelayOperationT_contra,
        context: ContextT_contra,
    ) -> None: ...

    async def exec_timeout(
        self,
        operation: TimeoutOperationT_contra,
        context: ContextT_contra,
    ) -> None: ...

    async def exec_retry(
        self,
        operation: RetryOperationT_contra,
        context: ContextT_contra,
    ) -> None: ...

    # Collection operations
    async def exec_map(
        self,
        operation: MapOperationT_contra,
        context: ContextT_contra,
    ) -> None: ...

    # Reactive operations
    async def exec_subscribe(
        self,
        operation: SubscribeOperationT_contra,
        context: ContextT_contra,
    ) -> None: ...


@runtime_checkable
class SyncExecutorProtocol(
    Protocol[
        SyncContextT_contra,
        OperationT_contra,
        AppOperationT_contra,
        BranchOperationT_contra,
        DelayOperationT_contra,
        FunctionOperationT_contra,
        LoopOperationT_contra,
        MapOperationT_contra,
        ParallelOperationT_contra,
        RetryOperationT_contra,
        SequenceOperationT_contra,
        SubscribeOperationT_contra,
        TimeoutOperationT_contra,
    ]
):
    """
    Protocol defining the sync interface for the execution engine.

    The execution engine is responsible for executing operations and
    providing them with context and services.
    """

    def execute(
        self,
        operation: OperationT_contra,
        parent_context: SyncContextT_contra | None = None,
    ) -> None: ...

    def exec_operation(
        self,
        context: SyncContextT_contra,
    ) -> None: ...

    # Atomic operations
    def exec_function(
        self,
        operation: FunctionOperationT_contra,
        context: SyncContextT_contra,
    ) -> None: ...

    def exec_app(
        self,
        operation: AppOperationT_contra,
        context: SyncContextT_contra,
    ) -> None: ...

    # Flow control operations
    def exec_sequence(
        self,
        operation: SequenceOperationT_contra,
        context: SyncContextT_contra,
    ) -> None: ...

    def exec_parallel(
        self,
        operation: ParallelOperationT_contra,
        context: SyncContextT_contra,
    ) -> None: ...

    def exec_branch(
        self,
        operation: BranchOperationT_contra,
        context: SyncContextT_contra,
    ) -> None: ...

    def exec_loop(
        self,
        operation: LoopOperationT_contra,
        context: SyncContextT_contra,
    ) -> None: ...

    # Timing operations
    def exec_delay(
        self,
        operation: DelayOperationT_contra,
        context: SyncContextT_contra,
    ) -> None: ...

    def exec_timeout(
        self,
        operation: TimeoutOperationT_contra,
        context: SyncContextT_contra,
    ) -> None: ...

    def exec_retry(
        self,
        operation: RetryOperationT_contra,
        context: SyncContextT_contra,
    ) -> None: ...

    # Collection operations
    def exec_map(
        self,
        operation: MapOperationT_contra,
        context: SyncContextT_contra,
    ) -> None: ...

    # Reactive operations
    def exec_subscribe(
        self,
        operation: SubscribeOperationT_contra,
        context: SyncContextT_contra,
    ) -> None: ...
