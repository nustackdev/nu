"""
Flow operation execution engine.

This module provides execution capabilities for flow operations such as
Sequence, which control the flow of execution through multiple operations.
"""

from __future__ import annotations

from loomi.interfaces.state.type_vars import StateDictT, StateT

from ..context.context import Context
from ..operations.sequence import Sequence
from .base import EngineBase


class FlowEngine(EngineBase[StateT, StateDictT]):
    """
    Engine mixin for executing flow control operations.

    Provides implementation for executing operations like Sequence that
    control the flow of execution through multiple child operations.
    Future implementations will include Parallel, Branch, Loop, etc.
    """

    async def exec_sequence(
        self, operation: Sequence[StateDictT], context: Context[StateDictT]
    ) -> None:
        """
        Execute a Sequence operation.

        Executes each child operation in sequence, waiting for each to complete
        before starting the next. Propagates context appropriately to each child.

        Args:
            operation: The Sequence operation to execute
            context: The execution context

        Raises:
            Exception: Any exception raised by child operations (if error_behavior is "fail")
        """
        self.logger.debug(f"Executing sequence of {len(operation.children)} operations")

        # Execute each child operation in sequence
        for i, child_op in enumerate(operation.children):
            self.logger.debug(f"Executing sequence item {i + 1}/{len(operation.children)}")

            # Create a derived context for the child operation
            # This maintains the scope but sets the operation reference correctly
            child_context = context.derive(operation=child_op)

            # Execute the child operation
            await self.exec_operation(child_context)
