from __future__ import annotations

from abc import ABC, abstractmethod
from copy import deepcopy
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from loomi.app.base import AsyncApp
    from loomi.app.handlers.state.protocols_tree import AsyncStateDictProtocol
    from loomi.app.handlers.tasks.protocols import AsyncOperationProtocol


class BaseOperation(ABC):
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
    async def execute(self, app: "AsyncApp", loc: "AsyncStateDictProtocol") -> None:
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

    @property
    def context(self) -> dict:
        """Return the context of the operation.

        This is a placeholder method to be overridden by subclasses.
        """
        if not hasattr(self, "_context"):
            # Initialize context if not already set
            # This allows subclasses to access the context without needing
            # to call the setter method explicitly
            self._context = {}
        # Return the context dictionary
        return self._context

    @context.setter
    def context(self, value: dict[str, Any]) -> None:
        """Set the context of the operation.

        This is a placeholder method to be overridden by subclasses.
        """
        self._context = value

    def update_context(self, context: dict[str, Any]) -> None:
        """Inject a context dictionary into the operation.

        This method allows for setting the context of the operation
        from an external source. It can be useful for testing or
        when the context needs to be set before execution.

        Args:
            context: Context dictionary to inject into the operation
        """
        if not isinstance(context, dict):
            raise TypeError("Context must be a dictionary")

        if not context or len(context) == 0:
            return

        for key, value in deepcopy(context).items():
            self.context[key] = value

    async def _execute_child(
        self, operation: "AsyncOperationProtocol", app: "AsyncApp", loc: "AsyncStateDictProtocol"
    ) -> None:
        """
        Execute a child operation by preserving the context.
        """
        operation.update_context(self.context)
        await operation.execute(app, loc)
