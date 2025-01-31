"""Service operations mixin implementations."""

from __future__ import annotations

from typing import Any, Callable

from sonny.service import BaseService

from ..exceptions import ExecutionError
from .protocols import OperationProtocol


class ServiceExecutionFeatureMixin(BaseService):
    """
    Service feature implementing operation capabilities.
    """

    @property
    def executor(self):
        """Check if service is stateful."""
        if not hasattr(self, "_executor_"):
            raise ExecutionError("No executor configured")
        return getattr(self, "_executor_")

    @property
    def e(self):
        """Short alias for state adapter."""
        return self.executor

    async def execute(
        self,
        operation: OperationProtocol,
    ) -> Any:
        """Execute operation."""
        return await self.e.execute(operation)

    def function(self, func: Callable, *, name: str | None = None) -> OperationProtocol:
        """Create function operation."""
        return self.e.function(func, name=name)

    def sequence(
        self, *operations: OperationProtocol, delay: float = 0, continue_on_error: bool = False
    ) -> OperationProtocol:
        """Create function operation."""
        return self.e.sequence(*operations, delay=delay, continue_on_error=continue_on_error)

    def repeat(
        self,
        operation: OperationProtocol,
        times: int | None = None,
        while_key: str | tuple[str, ...] | None = None,
        max_iterations: int | None = None,
        delay: float = 0,
        ignore_errors: bool = False,
    ) -> OperationProtocol:
        """Create repeat operation."""
        return self.e.repeat(
            operation,
            times=times,
            while_key=while_key,
            max_iterations=max_iterations,
            delay=delay,
            ignore_errors=ignore_errors,
        )

    def parallel(
        self,
        *operations: OperationProtocol,
        max_concurrent: int | None = None,
        timeout: float | None = None,
        ignore_errors: bool = False,
    ) -> OperationProtocol:
        """Create parallel operation."""
        return self.e.parallel(
            *operations,
            max_concurrent=max_concurrent,
            timeout=timeout,
            ignore_errors=ignore_errors,
        )


#     async def execute(self) -> None:
#         """Execute the chain workflow.

#         This method:
#         1. Initializes chain state
#         2. Calls setup
#         3. Executes the defined workflow
#         4. Handles cleanup
#         5. Manages errors and logging

#         Raises:
#             ChainError: If chain execution fails
#         """
#         logger.info(f"Starting chain execution: {self.name}")

#         try:
#             # Initialize state
#             await self._initialize_state()
#             # await self.store.set((self.key, "status"), value="running")
#             # await self.store.set((self.key, "start_time"), value="now")  # Use actual timestamp

#             # Setup
#             try:
#                 await self.setup()
#             except Exception as e:
#                 logger.error("Chain setup failed", exc_info=True)
#                 raise ChainError("Setup failed") from e

#             # Get and validate operation
#             if self._operation is None:
#                 self._operation = self.define()

#             if not isinstance(self._operation, OperationProtocol):
#                 raise ChainError(
#                     f"Chain definition must return an Operation, " f"got {type(self._operation)}"
#                 )

#             # Execute operation
#             try:
#                 await self._operation.execute(self)
#             except Exception as e:
#                 logger.error("Chain operation execution failed", exc_info=True)
#                 raise ChainError("Operation execution failed") from e

#             # Update state on success
#             # await self.store.update(f"{self._state_key}.status", value="completed")
#             # await self.store.update(
#             #     f"{self._state_key}.end_time", value="now"  # Use actual timestamp
#             # )
#             logger.info(f"Chain completed successfully: {self.name}")

#         except Exception as e:
#             # Update state on error
#             # await self.store.update(f"{self._state_key}.status", value="failed")
#             # await self.store.update(
#             #     f"{self._state_key}.end_time", value="now"  # Use actual timestamp
#             # )
#             # await self.store.update(f"{self._state_key}.error", value=str(e))

#             if not isinstance(e, ChainError):
#                 logger.error(f"Chain execution failed: {self.name}", exc_info=True)
#                 raise ChainError(f"Chain execution failed: {str(e)}") from e
#             raise

#         finally:
#             # Always attempt cleanup
#             try:
#                 await self.cleanup()
#                 await self._cleanup_state()
#             except Exception as e:
#                 logger.error("Chain cleanup failed", exc_info=True)
#                 if not isinstance(e, ChainError):
#                     raise ChainError("Cleanup failed") from e
#                 raise
