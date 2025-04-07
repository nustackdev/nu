from __future__ import annotations

from typing import Any, List, Protocol

from ..context import RuntimeContext
from ..meta import OperationMetadata


class Operation(Protocol):
    """
    Protocol defining the interface for all operations.

    Operations are declarative structures that define what work should be done.
    They are executed by the execution engine and its services.
    """

    @property
    def metadata(self) -> OperationMetadata:
        """
        Get the operation's metadata including type, description, and custom properties.
        Used for introspection, visualization, and execution planning.
        """
        ...

    def get_children(self) -> List["Operation"]:
        """
        Get all child operations of this operation.

        Returns:
            List of child operations, or empty list if none
        """
        ...

    async def execute(self, context: RuntimeContext) -> Any:
        """
        Execute the operation within the given context.

        This method is called by the execution engine when the operation
        is to be executed as part of a workflow.

        Args:
            context: Execution context providing access to state and services

        Returns:
            The result of the operation execution
        """
        ...
