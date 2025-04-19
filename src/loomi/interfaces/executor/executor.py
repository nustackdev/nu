from __future__ import annotations

from typing import Protocol, runtime_checkable

from .type_vars import (
    ContextT_contra,
    FunctionOperationT_contra,
    OperationT_contra,
    SequenceOperationT_contra,
    SyncContextT_contra,
)


@runtime_checkable
class AsyncExecutorProtocol(
    Protocol[
        ContextT_contra,
        OperationT_contra,
        FunctionOperationT_contra,
        SequenceOperationT_contra,
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

    async def exec_function(
        self,
        operation: FunctionOperationT_contra,
        context: ContextT_contra,
    ) -> None: ...

    async def exec_sequence(
        self,
        operation: SequenceOperationT_contra,
        context: ContextT_contra,
    ) -> None: ...


@runtime_checkable
class SyncExecutorProtocol(
    Protocol[
        SyncContextT_contra,
        OperationT_contra,
        FunctionOperationT_contra,
        SequenceOperationT_contra,
    ]
):
    """
    Protocol defining the async interface for the execution engine.

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

    def exec_function(
        self,
        operation: FunctionOperationT_contra,
        context: SyncContextT_contra,
    ) -> None: ...

    def exec_sequence(
        self,
        operation: SequenceOperationT_contra,
        context: SyncContextT_contra,
    ) -> None: ...
