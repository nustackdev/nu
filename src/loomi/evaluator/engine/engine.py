"""
Async execution engine for the expressions framework.

This module provides the ExecutionEngine, which is the central orchestrator
for expression execution. It combines the functionality of specialized engine
components to provide a complete execution environment.
"""

from __future__ import annotations

from typing import ParamSpec

import attrs

from loomi.attach import Attach
from loomi.service import SyncService
from loomi.spec import Spec
from loomi.state.interface.state import AsyncStateProtocol, SyncStateProtocol
from loomistd.state import StateSpec

from ..context import Context
from ..expressions import Branch, Function, Loop, Map, Parallel, Sequence, Subscribe
from ..services.logging import LoggingService, LoggingServiceSpec
from .atom import AtomEngine
from .flow import FlowEngine

P = ParamSpec("P")


class Evaluator(
    AtomEngine,
    FlowEngine,
    SyncService,
):
    """
    Central orchestrator for expression execution.

    This engine combines specialized components for different expression types
    to provide a complete execution environment. It serves as the primary entry
    point for executing expressions within the framework.

    The engine manages the execution lifecycle, provides expressions with context
    and access to services, and ensures consistent error handling and logging.

    Attributes:
        state: The state store to use for expressions
        executor: Service for executing expressions
        tracing: Service for tracing expression execution
        logger: Service for logging expression events
    """

    # --- Service specifications --- #

    state_service: AsyncStateProtocol | SyncStateProtocol = Attach()
    logger: LoggingService = Attach()
    # tracing: TracingService = Attach()

    # --- Expressions --- #

    Branch: type[Branch] = Branch
    Function: type[Function] = Function
    Loop: type[Loop] = Loop
    Map: type[Map] = Map
    Parallel: type[Parallel] = Parallel
    Sequence: type[Sequence] = Sequence
    Subscribe: type[Subscribe] = Subscribe

    # def Compound(
    #     self,
    #     op: Callable[Concatenate[Evaluator, P], Expression],
    # ) -> Callable[P, Expression]:
    #     """
    #     A decorator factory that injects an executor engine into a function.

    #     This decorator allows the creation of complex, composite expressions
    #     by giving the decorated function direct access to the engine.

    #     Args:
    #         engine: The executor engine to inject into the decorated function

    #     Returns:
    #         A decorator that injects the engine into the decorated function

    #     Example:
    #         >>> @compound(my_engine)
    #         >>> def ReactiveMap(op, *, items_path, max_concurrency=1, error_behavior="fail", on_fail=None):
    #         >>>     # Now has access to `my_engine` without having to pass it as an argument
    #         >>>     return my_engine.Sequence(...)
    #     """

    #     @wraps(op)
    #     def wrapper(*args: Any, **kwargs: Any) -> Expression:
    #         # Call the original function with the engine as the first argument
    #         return op(self, *args, **kwargs)

    #     return wrapper

    # --- Initialization and cleanup methods --- #

    # async def setup(self):
    #     """
    #     Setup the execution engine.

    #     This method sets up the engine, initializes services, and prepares
    #     for expression execution. It should be called before executing any
    #     expressions.
    #     """
    #     await self.setup_reactive()

    # async def cleanup(self):
    #     """
    #     Cleanup the engine and clean up resources.

    #     This method ensures that all active expressions are completed and
    #     resources are released properly.
    #     """
    #     await self.cleanup_reactive()

    # --- Execution methods --- #

    def exec_expression(self, context: Context) -> None:
        """
        Execute an expression with its context.

        This method overrides the base implementation to ensure proper dispatch
        to the specialized execution methods based on expression type.

        Args:
            context: Execution context providing access to state and services

        Raises:
            ExpressionError: If the expression execution fails
        """
        # For now, we use the base implementation
        # In the future, we might customize this method to add additional
        # functionality specific to the combined engine
        super().exec_expression(context)


@attrs.define(frozen=True, slots=True, kw_only=True)
class EvaluatorSpec(Spec):
    """
    Specification for the ExecutionEngine.

    This specification defines the configuration and dependencies for the
    ExecutionEngine.
    """

    name: str = "execution_engine"
    factory: type = Evaluator
    state_service: Spec = attrs.field(factory=lambda: StateSpec())
    logger: Spec = attrs.field(factory=lambda: LoggingServiceSpec())
