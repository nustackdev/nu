"""
Execution engine for the operations framework.

This module provides the ExecutionEngine, which is the central orchestrator
for operation execution. It combines the functionality of specialized engine
components to provide a complete execution environment.
"""

from __future__ import annotations

import anytree

from loomi import AsyncService, Attach
from loomi.interfaces.state.type_vars import StateDictT, StateT

from ..context.context import Context
from ..operations.base import Operation
from ..services.logging import LoggingService
from ..services.task_execution import TaskExecutionService
from ..services.tracing import TracingService
from .atom import AtomEngine
from .flow import FlowEngine


class ExecutionEngine(AsyncService, AtomEngine[StateT, StateDictT], FlowEngine[StateT, StateDictT]):
    """
    Central orchestrator for operation execution.

    This engine combines specialized components for different operation types
    to provide a complete execution environment. It serves as the primary entry
    point for executing operations within the framework.

    The engine manages the execution lifecycle, provides operations with context
    and access to services, and ensures consistent error handling and logging.

    Attributes:
        state: The state store to use for operations
        executor: Service for executing operations
        tracing: Service for tracing operation execution
        logger: Service for logging operation events
    """

    state: StateT = Attach()
    executor = Attach(TaskExecutionService)
    tracing = Attach(TracingService)
    logger = Attach(LoggingService)

    async def exec_operation(self, context: Context[StateDictT]) -> None:
        """
        Execute an operation with its context.

        This method overrides the base implementation to ensure proper dispatch
        to the specialized execution methods based on operation type.

        Args:
            context: Execution context providing access to state and services

        Raises:
            OperationError: If the operation execution fails
        """
        # For now, we use the base implementation
        # In the future, we might customize this method to add additional
        # functionality specific to the combined engine
        await super().exec_operation(context)

    def render_tree(self, tree: Operation[StateDictT]) -> str:
        """
        Render an operation tree as a string visualization.

        This utility method produces a string representation of the operation
        tree for debugging and visualization purposes.

        Args:
            tree: The root operation of the tree to render

        Returns:
            A string visualization of the operation tree
        """
        result = []
        for pre, _, node in anytree.RenderTree(tree):
            # Get node name
            node_name = node.__class__.__name__

            # Add function name if available
            func_name = ""
            if hasattr(node, "_func"):
                func_name = getattr(node._func, "__name__", str(node._func))
                if func_name:
                    func_name = f" {func_name}"

            # Add to result
            result.append(f"{pre}{node_name}{func_name}")

        return "\n".join(result)

    def render(self, tree: Operation[StateDictT]) -> None:
        """
        Render and print an operation tree.

        This convenience method renders the operation tree and prints it
        to the console, useful for debugging and development.

        Args:
            tree: The root operation of the tree to render
        """
        print(self.render_tree(tree))
