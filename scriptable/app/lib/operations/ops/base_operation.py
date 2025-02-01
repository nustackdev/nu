from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from scriptable.app.base import AppSyncBase


class Operation(ABC):
    """Base class for all chain operations.

    All chain operations should inherit from this class and implement
    the execute method. Operations represent atomic units of work
    that can be composed into complex chains.

    The operation execution follows these principles:
    1. All state is managed through the store
    2. Operations should not share state directly
    3. Each operation is responsible for its own error handling
    4. Operations should log their execution progress
    5. Operations should maintain their state under _chain.<type>.<id> key

    Example:
        ```python
        class MyOperation(Operation):
            async def execute(self, chain: "Chain") -> None:
                try:
                    # Initialize state
                    await chain.store.set("_chain.my_op.123", {"status": "running"})

                    # Execute operation
                    result = await some_work()
                    await chain.store.set("my_result", result)

                    # Update operation state
                    await chain.store.update("_chain.my_op.123.status",
                                           value="completed")
                except Exception as e:
                    await chain.store.update("_chain.my_op.123.status",
                                           value="failed")
                    raise OperationError("Operation failed") from e
        ```
    """

    @abstractmethod
    def execute(self, app: "AppSyncBase") -> None:
        """Execute the operation.

        This method should:
        1. Initialize operation state in store
        2. Execute the operation logic
        3. Update operation state
        4. Handle and propagate errors appropriately
        5. Log execution progress

        Args:
            chain: Chain instance providing access to the store

        Raises:
            OperationError: If operation execution fails
        """
        ...

    def __repr__(self) -> str:
        return f"Operation({self.__class__.__name__})"
