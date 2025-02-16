from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Optional

from ..exceptions import OperationError
from .base_operation import BaseOperation
from .logger import logger

if TYPE_CHECKING:
    from loomi.app.base import SyncApp


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
        class DataProc(App):
            def process_data(self):
                await self.store.set("data.status", "processed")

            def define(self) -> Operation:
                return FunctionOperation(self.process_data)

        # Or with standalone function
        def handle_data():
            ...

        op = FunctionOperation(handle_data, name="data_handler")
        ```

    Internal State:
        - Tracks execution status under _app.function.<id>
        - Records execution time and result status
    """

    def __init__(self, func: Callable[..., Any], *, name: Optional[str] = None) -> None:
        if not callable(func):
            raise ValueError("FunctionOperation requires a callable")

        self.func = func
        self.name = name or getattr(func, "__name__", str(func))
        self._id = hex(id(self))[2:]

        # Get function's module for better logging
        self._module = getattr(func, "__module__", "unknown")

    def _initialize_state(self, app: "SyncApp") -> None:
        """Initialize function execution state in store"""
        pass

    def execute(self, app: "SyncApp") -> None:
        """Execute the wrapped function."""
        logger.info(f"Executing function: {self.name}")

        try:
            self._initialize_state(app)

            try:
                self.func()
                logger.info(f"Function '{self.name}' completed successfully")
            except Exception as e:
                error_msg = f"Function '{self.name}' failed: {str(e)}"
                logger.error(error_msg, exc_info=True)
                raise OperationError(error_msg) from e
        except Exception as e:
            if not isinstance(e, OperationError):
                logger.error(f"Function operation '{self.name}' failed", exc_info=True)
                raise OperationError(f"Function operation failed: {str(e)}") from e
            raise
