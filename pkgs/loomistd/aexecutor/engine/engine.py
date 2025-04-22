"""
Execution engine for the operations framework.

This module provides the ExecutionEngine, which is the central orchestrator
for operation execution. It combines the functionality of specialized engine
components to provide a complete execution environment.
"""

from __future__ import annotations

from functools import wraps
from typing import TYPE_CHECKING, Any, Callable, Concatenate, ParamSpec

from loomi.attr import UseService
from loomi.interfaces.executor.executor import AsyncExecutorProtocol
from loomi.interfaces.state.type_vars import StateDictT, StateT
from loomi.service import AsyncService
from loomi.spec import Spec, SpecField
from loomistd.state import StateSpec

from ..context import Context
from ..operations import (
    App,
    Branch,
    Delay,
    Function,
    Loop,
    Map,
    Parallel,
    Retry,
    Sequence,
    Subscribe,
    Timeout,
)
from ..services.logging import LoggingService, LoggingServiceSpec
from ..services.task_execution import TaskExecutionService, TaskExecutionServiceSpec
from ..services.tracing import TracingService, TracingServiceSpec
from .atom import AtomEngine
from .base import Operation
from .collections import CollectionEngine
from .flow import FlowEngine
from .reactive import ReactiveEngine
from .timing import TimingEngine

P = ParamSpec("P")


class ExecutionEngine(
    AsyncService,
    AtomEngine[StateT, StateDictT],
    FlowEngine[StateT, StateDictT],
    TimingEngine[StateT, StateDictT],
    CollectionEngine[StateT, StateDictT],
    ReactiveEngine[StateT, StateDictT],
):
    """
    Central orchestrator for operation execution.

    This engine combines specialized components for different operation types
    to provide a complete execution environment. It serves as the primary entry
    point for executing operations within the framework.

    The engine manages the execution lifecycle, provides operations with context
    and access to services, and ensures consistent error handling and logging.

    Attributes:
        state: The state store to use for operations
        executor: Service for executing operations
        tracing: Service for tracing operation execution
        logger: Service for logging operation events
    """

    # --- Service specifications --- #

    state: StateT = UseService()
    executor: TaskExecutionService = UseService()
    tracing: TracingService = UseService()
    logger: LoggingService = UseService()

    # --- Operations --- #

    App: type[App[StateDictT]] = App
    Branch: type[Branch[StateDictT]] = Branch
    Delay: type[Delay[StateDictT]] = Delay
    Function: type[Function[StateDictT]] = Function
    Loop: type[Loop[StateDictT]] = Loop
    Map: type[Map[StateDictT]] = Map
    Parallel: type[Parallel[StateDictT]] = Parallel
    Retry: type[Retry[StateDictT]] = Retry
    Sequence: type[Sequence[StateDictT]] = Sequence
    Subscribe: type[Subscribe[StateDictT]] = Subscribe
    Timeout: type[Timeout[StateDictT]] = Timeout

    def Compound(
        self,
        op: Callable[Concatenate[ExecutionEngine, P], Operation],
    ) -> Callable[P, Operation]:
        """
        A decorator factory that injects an executor engine into a function.

        This decorator allows the creation of complex, composite operations
        by giving the decorated function direct access to the engine.

        Args:
            engine: The executor engine to inject into the decorated function

        Returns:
            A decorator that injects the engine into the decorated function

        Example:
            >>> @compound(my_engine)
            >>> def ReactiveMap(op, *, items_path, max_concurrency=1, error_behavior="fail", on_fail=None):
            >>>     # Now has access to `my_engine` without having to pass it as an argument
            >>>     return my_engine.Sequence(...)
        """

        @wraps(op)
        def wrapper(*args: Any, **kwargs: Any) -> Operation:
            # Call the original function with the engine as the first argument
            return op(self, *args, **kwargs)

        return wrapper

    # --- Initialization and cleanup methods --- #

    async def setup(self):
        """
        Setup the execution engine.

        This method sets up the engine, initializes services, and prepares
        for operation execution. It should be called before executing any
        operations.
        """
        await self.setup_reactive()

    async def cleanup(self):
        """
        Cleanup the engine and clean up resources.

        This method ensures that all active operations are completed and
        resources are released properly.
        """
        await self.cleanup_reactive()

    # --- Execution methods --- #

    async def exec_operation(self, context: Context[StateDictT]) -> None:
        """
        Execute an operation with its context.

        This method overrides the base implementation to ensure proper dispatch
        to the specialized execution methods based on operation type.

        Args:
            context: Execution context providing access to state and services

        Raises:
            OperationError: If the operation execution fails
        """
        # For now, we use the base implementation
        # In the future, we might customize this method to add additional
        # functionality specific to the combined engine
        await super().exec_operation(context)


class ExecutionEngineSpec(Spec):
    """
    Specification for the ExecutionEngine.

    This specification defines the configuration and dependencies for the
    ExecutionEngine.
    """

    name: str = SpecField(default="execution_engine")
    factory: type = SpecField(default=ExecutionEngine)
    state: Spec = SpecField(default=StateSpec())
    executor: Spec = SpecField(default=TaskExecutionServiceSpec())
    logger: Spec = SpecField(default=LoggingServiceSpec())
    tracing: Spec = SpecField(default=TracingServiceSpec())


if TYPE_CHECKING:
    _: type[
        AsyncExecutorProtocol[
            ExecutionEngine,
            Context,
            Operation,
            App,
            Branch,
            Delay,
            Function,
            Loop,
            Map,
            Parallel,
            Retry,
            Sequence,
            Subscribe,
            Timeout,
        ]
    ] = ExecutionEngine
