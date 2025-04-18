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
from .timing import TimingEngine


class ExecutionEngine(
    AsyncService,
    AtomEngine[StateT, StateDictT],
    FlowEngine[StateT, StateDictT],
    TimingEngine[StateT, StateDictT],
):
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

    def render_tree(self, tree: Operation[StateDictT]) -> str:  # noqa: C901
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

            # Add function name if available for Function operations
            func_name = ""
            if hasattr(node, "_func"):
                func_name = getattr(node._func, "__name__", str(node._func))
                if func_name:
                    func_name = f" {func_name}"

            # Add operation-specific information
            extra_info = ""

            # Flow operations
            if hasattr(node, "branch_ops") and hasattr(node, "condition"):
                if node.condition:
                    extra_info = " (condition_func)"
                elif node.condition_path:
                    extra_info = f" (condition_path={node.condition_path})"
            elif hasattr(node, "loop_op") and hasattr(node, "max_iterations"):
                if node.max_iterations:
                    extra_info = f" (max_iterations={node.max_iterations})"
                if node.condition:
                    extra_info += " (condition_func)"
                elif node.condition_path:
                    extra_info += f" (condition_path={node.condition_path})"
            elif hasattr(node, "max_concurrency"):
                extra_info = f" (max_concurrency={node.max_concurrency})"

            # Timing operations
            elif hasattr(node, "delay") and hasattr(node, "delay_path"):
                if callable(node.delay):
                    extra_info = " (delay_func)"
                elif node.delay is not None:
                    extra_info = f" (delay={node.delay}s)"
                elif node.delay_path:
                    extra_info = f" (delay_path={node.delay_path})"
            elif hasattr(node, "timeout") and hasattr(node, "timeout_op"):
                extra_info = f" (timeout={node.timeout}s)"
                if node.on_timeout:
                    extra_info += " with on_timeout"
            elif hasattr(node, "max_attempts") and hasattr(node, "retry_op"):
                extra_info = f" (max_attempts={node.max_attempts})"
                if node.retry_on:
                    retry_exceptions = [exc.__name__ for exc in node.retry_on]
                    extra_info += f" retry_on={retry_exceptions}"

            # Add to result
            result.append(f"{pre}{node_name}{func_name}{extra_info}")

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
