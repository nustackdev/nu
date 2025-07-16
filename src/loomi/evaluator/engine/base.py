"""
Base execution engine for the expressions framework.

This module provides the core engine functionality with lifecycle management,
error handling, and execution coordination. It serves as the foundation
for specialized expression executors.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional, cast

from frozendict import frozendict

from loomi.state.interface.state import AsyncStateServiceProtocol, SyncStateServiceProtocol
from loomi.state.interface.tree import AsyncStateProtocol, SyncStateProtocol

from ..context import Context
from ..expressions import (  # App,
    Branch,
    Expression,
    Function,
    Loop,
    Map,
    Parallel,
    Sequence,
    Subscribe,
)
from ..services.logging import LoggingService
from .exceptions import ExpressionConfigError, wrap_error


class EngineBase(ABC):
    """
    Base class for all expression execution engines.

    Provides core execution workflow, error handling, and lifecycle management.
    Specialized engines should inherit from this class and implement specific
    expression execution methods.

    Attributes:
        state: The state store service
        executor: Task execution service for managing tasks
        tracing: Service for tracing expression execution
        logger: Service for logging expression execution
    """

    # Services
    state_service: AsyncStateServiceProtocol | SyncStateServiceProtocol
    logger: LoggingService

    @property
    def state(self) -> AsyncStateProtocol | SyncStateProtocol:
        """
        Get the state service.

        This property should be overridden by subclasses to provide the actual
        state service instance.
        """
        return self.state_service.state

    def execute(
        self,
        expression: Expression,
        parent_context: Optional[Context] = None,
    ) -> None:
        """
        Execute an expression.

        This is the main entry point for executing expressions. It creates a new context
        if no parent context is provided, or derives a child context from the parent.

        Args:
            expression: The expression to execute
            parent_context: Optional parent context to derive from

        Raises:
            ExpressionConfigError: If the expression is invalid
            ExpressionError: If the expression execution fails
        """
        # Validate expression
        if not isinstance(expression, Expression):
            raise ExpressionConfigError(f"Expected Expression instance, got {type(expression)}")

        # Create root context for the expression
        context = Context(
            expression,
            frozendict(),  # Empty attributes dict
        )

        # self.tracing.start_execution(expression)

        try:
            # Execute the expression with its context
            self.exec_expression(context)
        finally:
            # Finalize tracing
            # self.tracing.end_execution()
            pass

    def exec_expression(self, context: Context) -> None:
        """
        Execute an expression with its context.

        This method handles the execution lifecycle including logging, tracing,
        and error handling. It dispatches to the appropriate specialized executor
        based on the expression type.

        Args:
            context: Execution context providing access to state and services

        Raises:
            ExpressionError: If the expression execution fails
        """
        expression = context.expression

        # Log expression start
        self.logger.log_expression_start(expression.metadata.name)

        # Initialize tracing if enabled
        # self.tracing.start_span(expression, context)

        try:
            # Dispatch to the appropriate execution method based on expression type
            # This will be extended as we add more expression types
            expression_type = type(expression)

            if expression_type is Function:
                self.exec_function(cast(Function, expression), context)
            elif expression_type is Sequence:
                self.exec_sequence(cast(Sequence, expression), context)
            # elif expression_type is Parallel:
            #     self.exec_parallel(cast(Parallel, expression), context)
            # elif expression_type is Branch:
            #     self.exec_branch(cast(Branch, expression), context)
            # elif expression_type is Loop:
            #     self.exec_loop(cast(Loop, expression), context)
            # elif expression_type is Map:
            #     self.exec_map(cast(Map, expression), context)
            # elif expression_type is Subscribe:
            #     self.exec_subscribe(cast(Subscribe, expression), context)
            else:
                self._exec_unknown(expression, context)

            # Log expression completion
            self.logger.log_expression_end(expression.metadata.name)

            # Finalize tracing
            # self.tracing.end_span(expression, context)

        except Exception as e:
            # Log the error
            self.logger.log_expression_error(expression.metadata.name, e)

            # Record error in tracing
            # self.tracing.record_exception(expression, context, e)

            # Handle on_fail expression if specified
            if expression._on_fail:
                fail_context = context.derive(expression._on_fail)
                try:
                    self.exec_expression(fail_context)
                except Exception as fail_e:
                    # Log error in on_fail handler
                    self.logger.log_expression_error(f"{expression.metadata.name}.on_fail", fail_e)

            # Handle error based on configured behavior
            if expression._error_behavior == "fail":
                wrapped = wrap_error(e, expression, context)
                raise wrapped

    @abstractmethod
    def exec_function(self, expression: Function, context: Context) -> None:
        """
        Execute a Function expression.

        Abstract method to be implemented by specialized engines.

        Args:
            expression: The Function expression to execute
            context: The execution context
        """
        pass

    @abstractmethod
    def exec_sequence(self, expression: Sequence, context: Context) -> None:
        """
        Execute a Sequence expression.

        Abstract method to be implemented by specialized engines.

        Args:
            expression: The Sequence expression to execute
            context: The execution context
        """
        pass

    # @abstractmethod
    # def exec_parallel(self, expression: Parallel, context: Context) -> None:
    #     """
    #     Execute a Parallel expression.

    #     Abstract method to be implemented by specialized engines.

    #     Args:
    #         expression: The Parallel expression to execute
    #         context: The execution context
    #     """
    #     pass

    # @abstractmethod
    # def exec_branch(self, expression: Branch, context: Context) -> None:
    #     """
    #     Execute a Branch expression.

    #     Abstract method to be implemented by specialized engines.

    #     Args:
    #         expression: The Branch expression to execute
    #         context: The execution context
    #     """
    #     pass

    # @abstractmethod
    # def exec_loop(self, expression: Loop, context: Context) -> None:
    #     """
    #     Execute a Loop expression.

    #     Abstract method to be implemented by specialized engines.

    #     Args:
    #         expression: The Loop expression to execute
    #         context: The execution context
    #     """
    #     pass

    # @abstractmethod
    # def exec_map(self, expression: Map, context: Context) -> None:
    #     """
    #     Execute a Map expression.

    #     Abstract method to be implemented by specialized engines.

    #     Args:
    #         expression: The Map expression to execute
    #         context: The execution context
    #     """
    #     pass

    # @abstractmethod
    # def exec_subscribe(self, expression: Subscribe, context: Context) -> None:
    #     """
    #     Execute a Subscribe expression.

    #     Abstract method to be implemented by specialized engines.

    #     Args:
    #         expression: The Subscribe expression to execute
    #         context: The execution context
    #     """
    #     pass

    def _exec_unknown(self, expression: Expression, context: Context) -> None:
        """
        Handle unknown expression types.

        This is a fallback method for expression types that are not explicitly supported.

        Args:
            expression: The unknown expression
            context: The execution context

        Raises:
            ExpressionConfigError: Always raised for unknown expressions
        """
        raise ExpressionConfigError(f"Unknown expression type: {expression.__class__.__name__}")
