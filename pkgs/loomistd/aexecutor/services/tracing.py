"""
Tracing Service.

This module provides the TracingService class which captures execution information
about operations and maintains a DAG representation for visualization purposes.
"""

import time
from typing import cast

from loomi import AsyncService, Spec, SpecField, UseService
from loomistd.state import State, StateSpec


class TracingService(AsyncService):
    """
    Service for tracing operation execution.

    Provides methods for recording trace events and retrieving trace information.
    """

    tracing_state: State = UseService()

    async def setup(self) -> None:
        """Initialize the tracing service."""
        self.state_path = ("_", "tracing")
        self._active_spans = {}  # Maps operation keys to span data
        self._registered_operations = set()  # Set of registered operation keys
        self._execution_start_time = None
        self._execution_end_time = None

    async def cleanup(self) -> None:
        """Shutdown the tracing service."""
        self._active_spans = {}
        self._registered_operations = set()

    async def post_initialize(self):
        """Initialize the tracing state structure."""
        # Create tracing state structure
        trace_root = await self.tracing_state.dict(*self.state_path)
        await trace_root.dict("operations")  # Complete operation records
        await trace_root.dict("execution")  # Currently executing operations
        await trace_root.dict("graph")  # DAG structure
        await trace_root.dict("metadata")  # Operation display metadata

    async def start_execution(self, root_operation):
        """
        Register an entire workflow DAG for visualization.

        Traverses the operation tree and registers all operations with the tracing system.
        This builds the initial graph structure before execution begins.

        Args:
            root_operation: The root operation of the workflow
        """

        # Record execution start time
        self._execution_start_time = time.time()

        # Get the graph dict from state
        graph_dict = await self.tracing_state.dict(*self.state_path, "graph")
        metadata_dict = await self.tracing_state.dict(*self.state_path, "metadata")

        # Track visited operations to avoid cycles
        visited = set()

        # Use recursive approach for DAG traversal
        async def register_operation(operation, parent_id=None):
            # Generate a unique key for this operation
            op_id = operation.key()

            # Skip if already visited (avoid cycles)
            if op_id in visited:
                return

            visited.add(op_id)
            self._registered_operations.add(op_id)

            # Get operation type and metadata
            op_type = operation.__class__.__name__
            op_metadata = operation.metadata

            # Store graph node information
            await graph_dict.set(
                op_id,
                value={
                    "type": op_type,
                    "name": op_metadata.name,
                    "parent": parent_id,
                    "children": [],
                },
            )

            # Store operation metadata for visualization
            await metadata_dict.set(
                op_id,
                value={
                    "display_name": getattr(op_metadata, "display_name", op_metadata.name),
                    "description": op_metadata.description,
                    "category": getattr(op_metadata, "category", None),
                    "icon": getattr(op_metadata, "icon", None),
                    "color": getattr(op_metadata, "color", None),
                    "custom_properties": op_metadata.custom_properties,
                },
            )

            # Update parent's children list
            if parent_id:
                parent_data: dict = cast(dict, await graph_dict.get(parent_id))
                if parent_data:
                    children = parent_data.get("children", [])
                    if op_id not in children:
                        children.append(op_id)
                        await graph_dict.set(parent_id, value={**parent_data, "children": children})

            # Recursively register children
            for child in operation.children:
                await register_operation(child, op_id)

        # Start registration from the root
        await register_operation(root_operation)

        # Store execution start time
        exec_root = await self.tracing_state.dict(*self.state_path)
        await exec_root.set("execution_start_time", value=self._execution_start_time)

    async def end_execution(self):
        """Finalize the tracing state and prepare for visualization."""
        # Record execution end time
        self._execution_end_time = time.time()

        # Calculate total execution time
        total_duration = 0
        if self._execution_start_time:
            total_duration = self._execution_end_time - self._execution_start_time

        # Store execution end time and duration in state
        exec_root = await self.tracing_state.dict(*self.state_path)
        await exec_root.set("execution_end_time", value=self._execution_end_time)
        await exec_root.set("execution_duration", value=total_duration)

        # Generate execution summary
        stats = await self._calculate_execution_stats()
        await exec_root.set("execution_summary", value=stats)

    async def start_span(self, operation, context):
        """
        Record the start of an operation execution.

        Args:
            operation: The operation that is starting
            context: The execution context
        """

        # Generate operation ID
        op_id = operation.key()

        # Register the operation if not already registered
        if op_id not in self._registered_operations:
            parent_op = None
            if hasattr(context, "parent") and context.parent:
                parent_op = context.parent.operation

            # Register operation in DAG
            root_op = operation
            while parent_op:
                root_op = parent_op
                parent_op = root_op.parent if hasattr(root_op, "parent") else None

            # Register the root operation
            await self.start_execution(root_op)

        # Record start time and basic information
        start_time = time.time()

        # Get parent operation ID if available
        parent_id = None
        if hasattr(context, "parent") and context.parent:
            parent_id = context.parent.operation.key()

        # Get operation metadata
        op_type = operation.__class__.__name__
        op_name = operation.metadata.name

        # Store span info in memory
        self._active_spans[op_id] = {
            "start_time": start_time,
            "op_type": op_type,
            "op_name": op_name,
            "status": "running",
            "parent_id": parent_id,
        }

        # Update execution state
        exec_dict = await self.tracing_state.dict(*self.state_path, "execution")
        await exec_dict.set(op_id, value=self._active_spans[op_id])

    async def end_span(self, operation, context, error=None):
        """
        Record the completion of an operation execution.

        Args:
            operation: The operation that completed
            context: The execution context
            error: Optional error that occurred during execution
        """

        # Generate operation ID
        op_id = operation.key()

        # Skip if the span wasn't started
        if op_id not in self._active_spans:
            return

        # Calculate execution time
        end_time = time.time()
        span_info = self._active_spans[op_id]
        duration = end_time - span_info["start_time"]

        # Update span info with completion data
        span_info["end_time"] = end_time
        span_info["duration"] = duration
        span_info["status"] = "error" if error else "completed"

        if error:
            span_info["error"] = str(error)
            span_info["error_type"] = error.__class__.__name__

        # Store in operations history
        ops_dict = await self.tracing_state.dict(*self.state_path, "operations")
        await ops_dict.set(op_id, value=span_info)

        # Remove from active execution
        exec_dict = await self.tracing_state.dict(*self.state_path, "execution")
        await exec_dict.delete(op_id)

        # Remove from active spans
        try:
            del self._active_spans[op_id]
        except KeyError:
            pass

    async def record_exception(self, operation, context, exception):
        """
        Record an exception that occurred during operation execution.

        Args:
            operation: The operation where the exception occurred
            context: The execution context
            exception: The exception that was raised
        """

        # Generate operation ID
        op_id = operation.key()

        # Skip if the span wasn't started
        if op_id not in self._active_spans:
            return

        # Update span info with error details
        self._active_spans[op_id]["status"] = "error"
        self._active_spans[op_id]["error"] = str(exception)
        self._active_spans[op_id]["error_type"] = exception.__class__.__name__

        # Update execution state
        exec_dict = await self.tracing_state.dict(*self.state_path, "execution")
        await exec_dict.set(op_id, value=self._active_spans[op_id])

    async def _calculate_execution_stats(self):
        """
        Calculate statistics about the workflow execution.

        Returns:
            Dict containing execution statistics
        """
        # Get required data
        graph_dict = await self.tracing_state.dict(*self.state_path, "graph")
        ops_dict = await self.tracing_state.dict(*self.state_path, "operations")
        exec_dict = await self.tracing_state.dict(*self.state_path, "execution")

        graph_data: dict = await graph_dict.to_dict()
        ops_data: dict = await ops_dict.to_dict()
        exec_data: dict = await exec_dict.to_dict()

        # Calculate statistics
        total_operations = len(graph_data)
        completed_operations = sum(1 for op in ops_data.values() if op.get("status") == "completed")
        failed_operations = sum(1 for op in ops_data.values() if op.get("status") == "error")
        running_operations = len(exec_data)
        pending_operations = (
            total_operations - completed_operations - failed_operations - running_operations
        )

        # Calculate timing statistics if available
        total_duration = 0
        min_duration = float("inf")
        max_duration = 0
        operation_durations = []

        for op in ops_data.values():
            if "duration" in op:
                duration = op["duration"]
                total_duration += duration
                min_duration = min(min_duration, duration)
                max_duration = max(max_duration, duration)
                operation_durations.append(duration)

        avg_duration = total_duration / len(operation_durations) if operation_durations else 0
        if min_duration == float("inf"):
            min_duration = 0

        return {
            "total": total_operations,
            "completed": completed_operations,
            "failed": failed_operations,
            "running": running_operations,
            "pending": pending_operations,
            "timing": {
                "total": total_duration,
                "average": avg_duration,
                "min": min_duration,
                "max": max_duration,
            },
        }


class TracingServiceSpec(Spec):
    """
    Specification for the TracingService.

    This specification defines the configuration and dependencies for the
    TracingService.
    """

    name: str = SpecField(default="tracing_service")
    factory: type = SpecField(default=TracingService)
    tracing_state: Spec = SpecField(default_factory=StateSpec)
