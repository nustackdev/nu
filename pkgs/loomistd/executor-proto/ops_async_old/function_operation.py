from __future__ import annotations

import asyncio
import inspect
from typing import TYPE_CHECKING, Any, Callable

from ..exceptions import OperationError
from .base_operation import BaseOperation
from .logger import logger

if TYPE_CHECKING:
    from loomi.app.base import AsyncApp
    from loomi.app.handlers.state.protocols_tree import AsyncStateDictProtocol


class FunctionOperation(BaseOperation):
    """Wraps a callable (function or method) as an operation.

    This is the fundamental building block that turns Python callables
    into app operations. Handles both sync and async functions.

    Args:
        func: Function or method to execute
        name: Optional name for the operation. If not provided,
            will use function's __name__ or str(func)

    Example:
        ```python
        class DataProc(Service):
            async def process_data(self):
                await self.store.set("data.status", "processed")

            def define(self) -> Operation:
                return FunctionOperation(self.process_data)

        # Or with standalone function
        async def handle_data():
            ...

        op = FunctionOperation(handle_data, name="data_handler")
        ```

    Internal State:
        - Tracks execution status under _app.function.<id>
        - Records execution time and result status
    """

    def __init__(self, func: Callable[..., Any], *, name: str | None = None) -> None:
        if not callable(func):
            raise ValueError("FunctionOperation requires a callable")

        self.func = func
        self.name = name or getattr(func, "__name__", str(func))
        self._id = hex(id(self))[2:]

        # Determine if function is async
        self._is_async = asyncio.iscoroutinefunction(func) or inspect.isasyncgenfunction(func)

        # Get function's module for better logging
        self._module = getattr(func, "__module__", "unknown")

    async def execute(self, app: "AsyncApp", loc: "AsyncStateDictProtocol") -> None:
        """Execute the wrapped function."""
        logger.info(f"Executing function: {self.name}")

        try:
            try:
                if self._is_async:
                    await self.func(context=self.context, loc=loc)
                else:
                    self.func(context=self.context, loc=loc)

                logger.info(f"Function '{self.name}' completed successfully")

            except Exception as e:
                error_msg = f"Function '{self.name}' failed: {str(e)}"
                logger.error(error_msg, exc_info=True)
                raise OperationError(error_msg) from e

        except asyncio.CancelledError:
            logger.info(f"Function '{self.name}' was cancelled")
            raise

        except Exception as e:
            if not isinstance(e, OperationError):
                logger.error(f"Function operation '{self.name}' failed", exc_info=True)
                raise OperationError(f"Function operation failed: {str(e)}") from e
            raise
