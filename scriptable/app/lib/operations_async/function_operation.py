import asyncio
import inspect
from typing import TYPE_CHECKING, Any, Callable, Optional

from ..exceptions import OperationError
from .base_operation import Operation
from .logger import logger

if TYPE_CHECKING:
    from sonny import AsyncService


class FunctionOperation(Operation):
    """Wraps a callable (function or method) as an operation.

    This is the fundamental building block that turns Python callables
    into service operations. Handles both sync and async functions.

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
        - Tracks execution status under _service.function.<id>
        - Records execution time and result status
    """

    def __init__(self, func: Callable[..., Any], *, name: Optional[str] = None) -> None:
        if not callable(func):
            raise ValueError("FunctionOperation requires a callable")

        self.func = func
        self.name = name or getattr(func, "__name__", str(func))
        self._id = hex(id(self))[2:]

        # Determine if function is async
        self._is_async = asyncio.iscoroutinefunction(func) or inspect.isasyncgenfunction(func)

        # Get function's module for better logging
        self._module = getattr(func, "__module__", "unknown")

    def _state_key(self, key: str | tuple[str, ...] | None = None) -> tuple[str, ...]:
        """Base key for function state in store"""
        if isinstance(key, str):
            key = (key,)
        return (
            (f"__service__function__{self._id}",) + key
            if key
            else (f"__service__function__{self._id}",)
        )

    async def _initialize_state(self, service: "AsyncService") -> None:
        """Initialize function execution state in store"""
        await service.state_set(
            self._state_key(),
            value={
                "status": "initialized",
                "name": self.name,
                "module": self._module,
                "is_async": self._is_async,
                "start_time": None,
                "end_time": None,
                "error": None,
            },
        )

    async def _execute_sync_func(self) -> Any:
        """Execute synchronous function in thread pool."""
        try:
            return await asyncio.to_thread(self.func)
        except Exception as e:
            logger.error(f"Sync function '{self.name}' failed in thread pool", exc_info=True)
            raise OperationError(f"Sync function execution failed: {str(e)}") from e

    async def execute(self, service: "AsyncService") -> None:
        """Execute the wrapped function."""
        logger.info(f"Executing function: {self.name}")

        try:
            await self._initialize_state(service)
            await service.state_set(self._state_key("status"), value="running")
            await service.state_set(
                self._state_key("start_time"), value="now"  # Use actual timestamp
            )

            try:
                if self._is_async:
                    await self.func()
                else:
                    await self._execute_sync_func()

                await service.state_set(self._state_key("status"), value="completed")
                await service.state_set(
                    self._state_key("end_time"), value="now"  # Use actual timestamp
                )
                logger.info(f"Function '{self.name}' completed successfully")

            except Exception as e:
                error_msg = f"Function '{self.name}' failed: {str(e)}"
                await service.state_set(self._state_key("status"), value="failed")
                await service.state_set(self._state_key("error"), value=error_msg)
                await service.state_set(
                    self._state_key("end_time"), value="now"  # Use actual timestamp
                )
                logger.error(error_msg, exc_info=True)
                raise OperationError(error_msg) from e

        except asyncio.CancelledError:
            await service.state_set(self._state_key("status"), value="cancelled")
            logger.info(f"Function '{self.name}' was cancelled")
            raise

        except Exception as e:
            if not isinstance(e, OperationError):
                logger.error(f"Function operation '{self.name}' failed", exc_info=True)
                raise OperationError(f"Function operation failed: {str(e)}") from e
            raise
