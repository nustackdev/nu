"""
Atomic operation execution engine.

This module provides the execution engine capabilities for atomic operations
such as Function and (in the future) App operations. Atomic operations are
the fundamental building blocks that don't contain child operations.
"""

from __future__ import annotations

import inspect

from loomi.interfaces.state.tree import AsyncStateProtocol, SyncStateProtocol
from loomi.interfaces.state.type_vars import StateT

from ..context.context import Context
from ..operations import App, Function
from .base import EngineBase
from .exceptions import StateAccessError


class AtomEngine(EngineBase[StateT]):
    """
    Engine mixin for executing atomic operations.

    Provides implementation for executing Function operations
    and (in the future) App operations. These operations represent
    the fundamental building blocks of workflows.
    """

    async def exec_function(self, operation: Function[StateT], context: Context[StateT]) -> None:
        """
        Execute a Function operation.

        Executes the callable function defined in the operation, providing it
        with the context. Handles both synchronous and asynchronous functions.

        Args:
            operation: The Function operation to execute
            context: The execution context

        Raises:
            Exception: Any exception raised by the function
        """
        # Get function metadata for logging
        func_name = getattr(operation._func, "__name__", "<anonymous>")
        self.logger.debug(f"Executing function {func_name}")

        # Execute the function through the task executor service
        await self.execute_task(operation._func, context)

    async def exec_app(self, operation: App[StateT], context: Context[StateT]) -> None:
        """
        Execute an App operation.

        Executes a Loomi app as an operation, optionally mounting it at a specific
        state path. Handles both synchronous and asynchronous apps.

        Args:
            operation: The App operation to execute
            context: The execution context

        Raises:
            StateAccessError: If the state path cannot be accessed
            Exception: Any exception raised by the app
        """
        app = operation.app
        state_path = operation.state_path

        app_name = getattr(app, "__class__", app).__name__
        self.logger.debug(f"Executing app {app_name}")

        # Handle state path mounting
        if state_path:
            self.logger.debug(f"Mounting app at state path: {state_path}")

            try:
                # Get the dictionary object
                if isinstance(context.scope, AsyncStateProtocol):
                    app_scope = await context.scope.at(*state_path)
                elif isinstance(context.scope, SyncStateProtocol):
                    app_scope = context.scope.at(*state_path)
                else:
                    raise StateAccessError(
                        f"Unsupported dict type: {type(context.scope)}",
                        operation=operation,
                    )

            except Exception as e:
                raise StateAccessError(
                    f"Failed to access state path {state_path}",
                    operation=operation,
                    context=context,
                    state_path=state_path,
                    cause=e,
                )
        else:
            # Use current context's scope
            app_scope = context.scope

        # Create a derived context for the app
        app_context = context.derive(operation=operation, scope=app_scope)

        # Execute the app
        if inspect.iscoroutinefunction(app.start):
            await app.start(app_context)
        else:
            app.start(app_context)

        self.logger.debug(f"App {app_name} execution completed")
