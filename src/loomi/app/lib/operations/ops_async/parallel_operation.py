from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Optional

from ..exceptions import OperationError
from .base_operation import BaseOperation
from .logger import logger

if TYPE_CHECKING:
    from loomi.app.base import AsyncApp
    from loomi.app.handlers.tasks import AsyncOperationProtocol


class ParallelOperation(BaseOperation):
    """Executes multiple operations concurrently.

    Args:
        operations: List of operations to execute in parallel
        max_concurrent: Maximum number of operations to run simultaneously
        timeout: Maximum time in seconds to wait for all operations
        ignore_errors: Whether to continue execution if an operation fails

    Example:
        ```python
        class ProcessMultipleItems(App):
            async def process_item_1(self):
                # Process logic here
                pass

            async def process_item_2(self):
                # Process logic here
                pass

            def define(self) -> Operation:
                return ParallelOperation(
                    operations=[
                        FunctionOperation(self.process_item_1),
                        FunctionOperation(self.process_item_2)
                    ],
                    max_concurrent=2,
                    timeout=60.0
                )
        ```

    Internal State:
        - Tracks operation status under __parallel__.<id>.status
        - Records completed operations under __parallel__.<id>.completed
        - Records errors under __parallel__.<id>.errors
        - Stores execution status and timing information
    """

    def __init__(
        self,
        *operations: "AsyncOperationProtocol",
        max_concurrent: Optional[int] = None,
        timeout: Optional[float] = None,
        ignore_errors: bool = False,
    ) -> None:
        if not operations:
            raise ValueError("At least one operation must be provided")
        if max_concurrent is not None and max_concurrent <= 0:
            raise ValueError("'max_concurrent' must be positive")
        if timeout is not None and timeout <= 0:
            raise ValueError("'timeout' must be positive")

        self.operations = operations
        self.max_concurrent = max_concurrent
        self.timeout = timeout
        self.ignore_errors = ignore_errors
        self._id = hex(id(self))[2:]

    async def _initialize_state(self, app: "AsyncApp") -> None:
        """Initialize parallel operation state in store"""
        pass

    async def _update_completed(self, app: "AsyncApp", completed: int) -> None:
        """Update count of completed operations in store"""

    async def _record_error(self, app: "AsyncApp", operation_index: int, error: Exception) -> None:
        """Record operation error in store"""
        error_data = {
            "operation_index": operation_index,
            "error": str(error),
            "error_type": error.__class__.__name__,
        }

    async def _execute_operation(
        self, app: "AsyncApp", operation: "AsyncOperationProtocol", index: int
    ) -> None:
        """Execute a single operation and handle its outcome"""
        try:
            await operation.execute(app)
        except Exception as e:
            error_msg = f"Operation {index} failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            await self._record_error(app, index, e)

            if not self.ignore_errors:
                raise OperationError(error_msg) from e

    async def execute(self, app: "AsyncApp") -> None:
        """Execute all operations in parallel within constraints."""
        logger.info(f"Starting parallel execution of {len(self.operations)} operations")

        try:
            await self._initialize_state(app)

            # Create semaphore if max_concurrent is specified
            semaphore = None
            if self.max_concurrent:
                semaphore = asyncio.Semaphore(self.max_concurrent)

            async def bounded_operation(op: "AsyncOperationProtocol", idx: int) -> None:
                if semaphore:
                    async with semaphore:
                        await self._execute_operation(app, op, idx)
                else:
                    await self._execute_operation(app, op, idx)

            # Create tasks for all operations
            tasks = [
                asyncio.create_task(bounded_operation(op, i))
                for i, op in enumerate(self.operations)
            ]

            # Wait for all tasks to complete
            try:
                await asyncio.wait_for(
                    asyncio.gather(*tasks, return_exceptions=self.ignore_errors),
                    timeout=self.timeout,
                )
            except asyncio.TimeoutError:
                error_msg = f"Parallel operation timed out after {self.timeout}s"
                logger.error(error_msg)
                raise OperationError(error_msg)

            logger.info("Parallel operation completed successfully")

        except asyncio.CancelledError:
            logger.info("Parallel operation was cancelled")
            raise

        except Exception as e:
            if not isinstance(e, OperationError):
                logger.error("Parallel operation failed", exc_info=True)
                raise OperationError(f"Parallel operation failed: {str(e)}") from e
            raise
