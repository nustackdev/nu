from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any, Awaitable, Callable

from ..exceptions import OperationError
from .base_operation import BaseOperation
from .logger import logger

if TYPE_CHECKING:
    from loomi.app.base import AsyncApp
    from loomi.app.handlers.state.protocols_tree import AsyncStateDictProtocol
    from loomi.app.handlers.state.types import StatePath
    from loomi.app.handlers.tasks import AsyncOperationProtocol


class ConditionalOperation(BaseOperation):
    """Executes an operation only if a specified condition evaluates to True.

    This operation can evaluate conditions in two ways:
    1. By checking a state key condition (if condition_key is provided)
    2. By executing a custom condition function (if condition_func is provided)

    Args:
        operation: Operation to execute if condition is True
        condition_key: State key to check for the condition (tuple of strings)
        condition_func: Function that returns a boolean result
        else_operation: Optional operation to execute if condition is False

    Example:
        ```python
        class ProcessIfEnabled(App):
            async def process_data(self):
                # Process logic here
                pass

            async def handle_disabled(self):
                # Alternative logic when processing is disabled
                pass

            async def check_condition(self):
                # Custom condition logic
                return await self.get(("user", "active")) and await self.get(("quota", "available"))

            # Using state key condition
            def define_with_key(self) -> Operation:
                return ConditionalOperation(
                    FunctionOperation(self.process_data),
                    condition_key=("settings", "processing_enabled"),
                    else_operation=FunctionOperation(self.handle_disabled),
                )

            # Using function condition
            def define_with_func(self) -> Operation:
                return ConditionalOperation(
                    FunctionOperation(self.process_data),
                    condition_func=self.check_condition,
                    else_operation=FunctionOperation(self.handle_disabled),
                )
        ```

    Internal State:
        - Tracks execution status and timing information
    """

    def __init__(
        self,
        operation: "AsyncOperationProtocol",
        *,
        condition_key: "StatePath | None" = None,
        condition_func: Callable[["AsyncStateDictProtocol"], Awaitable[bool | Any]] | None = None,
        else_operation: "AsyncOperationProtocol | None" = None,
    ) -> None:
        if condition_key is None and condition_func is None:
            raise ValueError("Either condition_key or condition_func must be provided")
        if condition_key is not None and condition_func is not None:
            raise ValueError("Cannot specify both condition_key and condition_func")

        self.operation = operation
        self.condition_key = condition_key
        self.condition_func = condition_func
        self.else_operation = else_operation
        self._id = hex(id(self))[2:]

    async def _evaluate_condition(self, app: "AsyncApp", loc: "AsyncStateDictProtocol") -> bool:
        """Evaluate the condition using either key or function."""
        if self.condition_key is not None:
            # Check the condition in the state
            condition_value = await loc.get(*self.condition_key)
            return bool(condition_value)
        elif self.condition_func is not None:
            # Execute the condition function
            result = await self.condition_func(loc)
            return bool(result)

        # This should never happen due to validation in __init__
        return False

    async def execute(self, app: "AsyncApp", loc: "AsyncStateDictProtocol") -> None:
        """Execute the operation if the condition is True."""
        condition_source = "key" if self.condition_key is not None else "function"
        condition_identifier = (
            self.condition_key
            if self.condition_key is not None
            else (
                getattr(self.condition_func, "__name__")
                if hasattr(self.condition_func, "__name__")
                else "anonymous"
            )
        )

        logger.info(
            f"Starting conditional operation with condition {condition_source}: {condition_identifier}"
        )

        try:
            # Evaluate the condition
            condition_value = await self._evaluate_condition(app, loc)

            if condition_value:
                logger.info("Condition is True, executing operation")

                await self._execute_child(self.operation, app, loc)
            else:
                logger.info("Condition is False")
                if self.else_operation:
                    logger.info("Executing else operation")
                    await self._execute_child(self.else_operation, app, loc)
                else:
                    logger.info("No else operation specified, skipping execution")

            logger.info("Conditional operation completed successfully")

        except asyncio.CancelledError:
            logger.info("Conditional operation was cancelled")
            raise

        except Exception as e:
            logger.error(f"Conditional operation failed: {str(e)}", exc_info=True)
            raise OperationError(f"Conditional operation failed: {str(e)}") from e
