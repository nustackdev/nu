from time import sleep
from typing import TYPE_CHECKING

from ..exceptions import OperationError
from .base_operation import Operation
from .logger import logger

if TYPE_CHECKING:
    from scriptable.app.base import AppSyncBase


class SequenceOperation(Operation):
    """Executes operations in sequence, one after another.

    Args:
        *operations: Operations to execute in sequence
        delay: Delay between operations in seconds. Defaults to 0.
        continue_on_error: Whether to continue execution if an operation fails.
            Defaults to False.

    Example:
        ```python
        class ProcessData(App):
            async def extract(self):
                await self.store.set("data", {"extracted": True})

            async def transform(self):
                await self.store.set("data.transformed", True)

            def define(self) -> Operation:
                return SequenceOperation(
                    FunctionOperation(self.extract),
                    FunctionOperation(self.transform),
                    delay=1.0
                )
        ```

    Internal State:
        - Stores execution status under __sequence__.<id>.current_step
        - Tracks errors under __sequence__.<id>.errors
    """

    def __init__(
        self, *operations: Operation, delay: float = 0, continue_on_error: bool = False
    ) -> None:
        self.operations = operations
        self.delay = delay
        self.continue_on_error = continue_on_error
        # Unique identifier for this sequence instance
        self._id = hex(id(self))[2:]

    def _state_key(self, key: str | tuple[str, ...] | None = None) -> tuple[str, ...]:
        """Base key for function state in store"""
        if isinstance(key, str):
            key = (key,)
        return (f"__app__sequence__{self._id}",) + key if key else (f"__app__sequence__{self._id}",)

    def _initialize_state(self, app: "AppSyncBase") -> None:
        """Initialize sequence state in store"""
        app.set(
            self._state_key(),
            value={
                "total_steps": len(self.operations),
                "current_step": 0,
                "errors": [],
                "status": "initialized",
            },
        )

    def _update_step(self, app: "AppSyncBase", step: int) -> None:
        """Update current execution step in store"""
        app.set(self._state_key("current_step"), value=step)
        app.set(self._state_key("status"), value="running")

    def _record_error(self, app: "AppSyncBase", step: int, error: Exception) -> None:
        """Record operation error in store"""
        error_data = {"step": step, "error": str(error), "error_type": error.__class__.__name__}
        app.set(self._state_key("errors"), value=lambda errors: [*errors, error_data])

    def execute(self, app: "AppSyncBase") -> None:
        """Execute operations in sequence with optional delay between them."""
        logger.info(f"Starting sequence execution of {len(self.operations)} operations")

        try:
            self._initialize_state(app)

            for i, operation in enumerate(self.operations):
                try:
                    self._update_step(app, i)
                    logger.debug(f"Executing sequence step {i + 1}/{len(self.operations)}")

                    operation.execute(app)

                    if i < len(self.operations) - 1 and self.delay > 0:
                        logger.debug(f"Waiting {self.delay}s before next operation")
                        sleep(self.delay)

                except Exception as e:
                    error_msg = f"Operation {i + 1} failed: {str(e)}"
                    logger.error(error_msg, exc_info=True)
                    self._record_error(app, i, e)

                    if not self.continue_on_error:
                        raise OperationError(error_msg) from e

            app.set(self._state_key("status"), value="completed")
            logger.info("Sequence execution completed successfully")

        except Exception as e:
            app.set(self._state_key("status"), value="failed")
            logger.error("Sequence execution failed", exc_info=True)
            raise OperationError("Sequence execution failed") from e
