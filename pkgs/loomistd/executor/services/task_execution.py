"""
Task execution service for managing and executing tasks in an asyncio environment.
This service provides concurrency control, task tracking, and cancellation management.
"""

from __future__ import annotations

import asyncio
import uuid
from typing import Any, Awaitable, Callable, Dict, Optional, TypeVar

from loomi.service import AsyncService, Spec

from ..context import Context
from .exceptions import TaskExecutionCancelledError, TaskExecutionTimeoutError
from .logger import logger

__all__ = [
    "TaskExecutionService",
    "TaskExecutionServiceSpec",
]

T = TypeVar("T")  # Generic type for task result


class TaskExecutionService(AsyncService):
    """
    Simple service for executing operation functions as managed asyncio tasks.

    Provides concurrency control, task tracking, and cancellation management.
    """

    spec: TaskExecutionServiceSpec

    async def setup(self) -> None:
        """Initialize service resources."""
        self._semaphore = asyncio.Semaphore(self.spec.max_concurrency)
        self._active_tasks: Dict[str, asyncio.Task] = {}
        self._results: Dict[str, Any] = {}

    async def cleanup(self) -> None:
        """Cancel all tasks and clean up resources."""
        await self.cancel_all_tasks()
        self._active_tasks.clear()
        self._results.clear()

    async def execute(
        self,
        func: Callable[[Context], Awaitable[T]],
        context: Context,
        timeout: Optional[float] = None,
        wait: bool = True,
    ) -> tuple[Optional[T], str]:
        """
        Execute a function as a managed task.

        Args:
            func: The async function to execute
            context: Context to pass to the function
            timeout: Optional timeout in seconds (0 means no timeout)
            wait: Whether to wait for completion

        Returns:
            Tuple of (result, task_id) if wait=True, otherwise (None, task_id)
        """
        task_id = str(uuid.uuid4())

        async def _run_task():
            try:
                async with self._semaphore:
                    start_time = asyncio.get_event_loop().time()
                    result = await func(context)
                    duration = (asyncio.get_event_loop().time() - start_time) * 1000
                    logger.debug(f"Task {task_id} completed in {duration:.2f}ms")
                    self._results[task_id] = result
                    return result
            except asyncio.CancelledError:
                logger.info(f"Task {task_id} was cancelled")
                raise TaskExecutionCancelledError(f"Task cancelled: {task_id}")
            finally:
                if task_id in self._active_tasks:
                    del self._active_tasks[task_id]

        # Create the task
        task = asyncio.create_task(_run_task(), name=f"task:{task_id}")
        self._active_tasks[task_id] = task

        if not wait:
            return None, task_id

        try:
            # Determine actual timeout
            actual_timeout = timeout if timeout is not None else self.spec.default_timeout

            # If timeout is 0, wait without a timeout
            if actual_timeout == 0:
                result = await task
            else:
                result = await asyncio.wait_for(task, actual_timeout)

            return result, task_id
        except asyncio.TimeoutError:
            task.cancel()
            raise TaskExecutionTimeoutError(f"Task timed out after {actual_timeout}s: {task_id}")

    async def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a specific task.

        Args:
            task_id: ID of the task to cancel

        Returns:
            True if task was found and cancelled, False otherwise
        """
        if task_id in self._active_tasks:
            task = self._active_tasks[task_id]
            if not task.done():
                task.cancel()
                return True
        return False

    async def cancel_all_tasks(self) -> int:
        """
        Cancel all running tasks.

        Returns:
            Number of tasks cancelled
        """
        count = 0
        for task_id, task in list(self._active_tasks.items()):
            if not task.done():
                task.cancel()
                count += 1
        return count

    async def wait_for_task(self, task_id: str, timeout: Optional[float] = None) -> Any:
        """
        Wait for a task to complete.

        Args:
            task_id: The task ID to wait for
            timeout: Optional timeout in seconds (0 means no timeout)

        Returns:
            Task result
        """
        if task_id not in self._active_tasks:
            if task_id in self._results:
                return self._results[task_id]
            raise ValueError(f"Task {task_id} not found")

        task = self._active_tasks[task_id]
        actual_timeout = timeout if timeout is not None else self.spec.default_timeout

        try:
            # If timeout is 0, wait without a timeout
            if actual_timeout == 0:
                return await task
            else:
                return await asyncio.wait_for(task, actual_timeout)
        except asyncio.TimeoutError:
            raise TaskExecutionTimeoutError(f"Waiting timed out after {actual_timeout}s")

    def get_active_task_count(self) -> int:
        """Get the number of active tasks."""
        return len(self._active_tasks)

    def get_task_result(self, task_id: str) -> Optional[Any]:
        """Get the result of a completed task."""
        return self._results.get(task_id)


class TaskExecutionServiceSpec(Spec):
    """Specification for the TaskExecutionService."""

    name: str = "task_execution_service"
    factory: type[AsyncService] = TaskExecutionService
    max_concurrency: int = 100
    default_timeout: float = 300.0
