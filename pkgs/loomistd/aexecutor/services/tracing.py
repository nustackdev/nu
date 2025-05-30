"""
Tracing Service.

This module provides the TracingService class which captures execution information
about operations and maintains a DAG representation for visualization purposes.
"""

from __future__ import annotations

from typing import Any

from loomi import AsyncService, Spec, SpecField, UseService
from loomi.interfaces.state.tree import AsyncStateProtocol, SyncStateProtocol
from loomistd.state import StateSpec


class TracingService(AsyncService):
    """
    Service for tracing operation execution.

    Provides methods for recording trace events and retrieving trace information.
    Supports both synchronous and asynchronous state implementations.
    """

    state: AsyncStateProtocol | SyncStateProtocol = UseService()

    spec: TracingServiceSpec

    async def setup(self) -> None:
        """Initialize the tracing service."""
        self._state_path = self.spec.state_root_path
        self._active_spans: dict[str, dict[str, Any]] = {}  # Maps operation keys to span data
        self._registered_operations: set[str] = set()  # Set of registered operation keys
        self._execution_start_time: float | None = None
        self._execution_end_time: float | None = None

    async def cleanup(self) -> None:
        """Shutdown the tracing service."""
        self._active_spans = {}
        self._registered_operations = set()

    # async def post_initialize(self):
    #     """Initialize the tracing state structure."""
    #     # Get the trace root based on state protocol
    #     trace_root = None
    #     if isinstance(self.state, AsyncStateProtocol):
    #         trace_root = await self.state.dict(*self._state_path)
    #     elif isinstance(self.state, SyncStateProtocol):
    #         trace_root = self.state.dict(*self._state_path)
    #     else:
    #         # Unsupported state protocol
    #         return

    #     # Create required dictionaries based on tree dict protocol
    #     if isinstance(trace_root, AsyncStateProtocol):
    #         await trace_root.dict("operations")  # Complete operation records
    #         await trace_root.dict("execution")  # Currently executing operations
    #         await trace_root.dict("graph")  # DAG structure
    #         await trace_root.dict("metadata")  # Operation display metadata
    #     elif isinstance(trace_root, SyncStateProtocol):
    #         trace_root.dict("operations")  # Complete operation records
    #         trace_root.dict("execution")  # Currently executing operations
    #         trace_root.dict("graph")  # DAG structure
    #         trace_root.dict("metadata")  # Operation display metadata

    # async def start_execution(self, root_operation):  # noqa: C901
    #     """
    #     Register an entire workflow DAG for visualization.

    #     Traverses the operation tree and registers all operations with the tracing system.
    #     This builds the initial graph structure before execution begins.

    #     Args:
    #         root_operation: The root operation of the workflow
    #     """
    #     # Record execution start time
    #     self._execution_start_time = time.time()

    #     # Get the dictionaries based on state protocol
    #     graph_dict = None
    #     metadata_dict = None
    #     if isinstance(self.state, AsyncStateProtocol):
    #         graph_dict = await self.state.dict(*self._state_path, "graph")
    #         metadata_dict = await self.state.dict(*self._state_path, "metadata")
    #     elif isinstance(self.state, SyncStateProtocol):
    #         graph_dict = self.state.dict(*self._state_path, "graph")
    #         metadata_dict = self.state.dict(*self._state_path, "metadata")
    #     else:
    #         # Unsupported state protocol
    #         return

    #     # Track visited operations to avoid cycles
    #     visited = set()

    #     # Use recursive approach for DAG traversal
    #     async def register_operation(operation, parent_id=None):
    #         # Generate a unique key for this operation
    #         op_id = operation.key()

    #         # Skip if already visited (avoid cycles)
    #         if op_id in visited:
    #             return

    #         visited.add(op_id)
    #         self._registered_operations.add(op_id)

    #         # Get operation type and metadata
    #         op_type = operation.__class__.__name__
    #         op_metadata = operation.metadata

    #         # Store graph node information
    #         node_data = {
    #             "type": op_type,
    #             "name": op_metadata.name,
    #             "parent": parent_id,
    #             "children": [],
    #         }

    #         # Set graph node data based on dict protocol
    #         if isinstance(graph_dict, AsyncStateProtocol):
    #             await graph_dict.set(op_id, value=node_data)
    #         elif isinstance(graph_dict, SyncStateProtocol):
    #             graph_dict.set(op_id, value=node_data)

    #         # Store operation metadata for visualization
    #         metadata_value = {
    #             "display_name": getattr(op_metadata, "display_name", op_metadata.name),
    #             "description": op_metadata.description,
    #             "category": getattr(op_metadata, "category", None),
    #             "icon": getattr(op_metadata, "icon", None),
    #             "color": getattr(op_metadata, "color", None),
    #             "custom_properties": op_metadata.custom_properties,
    #         }

    #         # Set metadata based on dict protocol
    #         if isinstance(metadata_dict, AsyncStateProtocol):
    #             await metadata_dict.set(op_id, value=metadata_value)
    #         elif isinstance(metadata_dict, SyncStateProtocol):
    #             metadata_dict.set(op_id, value=metadata_value)

    #         # Update parent's children list
    #         if parent_id:
    #             parent_data = None
    #             # Get parent data based on dict protocol
    #             if isinstance(graph_dict, AsyncStateProtocol):
    #                 parent_data = cast(dict, await graph_dict.get(parent_id))
    #             elif isinstance(graph_dict, SyncStateProtocol):
    #                 parent_data = cast(dict, graph_dict.get(parent_id))

    #             if parent_data:
    #                 children = parent_data.get("children", [])
    #                 if op_id not in children:
    #                     children.append(op_id)
    #                     updated_parent = {**parent_data, "children": children}

    #                     # Update parent based on dict protocol
    #                     if isinstance(graph_dict, AsyncStateProtocol):
    #                         await graph_dict.set(parent_id, value=updated_parent)
    #                     elif isinstance(graph_dict, SyncStateProtocol):
    #                         graph_dict.set(parent_id, value=updated_parent)

    #         # Recursively register children
    #         for child in operation.children:
    #             await register_operation(child, op_id)

    #     # Start registration from the root
    #     await register_operation(root_operation)

    #     # Store execution start time
    #     exec_root = None
    #     if isinstance(self.state, AsyncStateProtocol):
    #         exec_root = await self.state.dict(*self._state_path)
    #     elif isinstance(self.state, SyncStateProtocol):
    #         exec_root = self.state.dict(*self._state_path)

    #     # Set execution start time based on dict protocol
    #     if isinstance(exec_root, AsyncStateProtocol):
    #         await exec_root.set("execution_start_time", value=self._execution_start_time)
    #     elif isinstance(exec_root, SyncStateProtocol):
    #         exec_root.set("execution_start_time", value=self._execution_start_time)

    # async def end_execution(self):
    #     """Finalize the tracing state and prepare for visualization."""
    #     # Record execution end time
    #     self._execution_end_time = time.time()

    #     # Calculate total execution time
    #     total_duration = 0
    #     if self._execution_start_time:
    #         total_duration = self._execution_end_time - self._execution_start_time

    #     # Get the exec_root based on state protocol
    #     exec_root = None
    #     if isinstance(self.state, AsyncStateProtocol):
    #         exec_root = await self.state.dict(*self._state_path)
    #     elif isinstance(self.state, SyncStateProtocol):
    #         exec_root = self.state.dict(*self._state_path)
    #     else:
    #         # Unsupported state protocol
    #         return

    #     # Store execution data based on dict protocol
    #     if isinstance(exec_root, AsyncStateProtocol):
    #         await exec_root.set("execution_end_time", value=self._execution_end_time)
    #         await exec_root.set("execution_duration", value=total_duration)
    #     elif isinstance(exec_root, SyncStateProtocol):
    #         exec_root.set("execution_end_time", value=self._execution_end_time)
    #         exec_root.set("execution_duration", value=total_duration)

    #     # Generate execution summary
    #     stats = await self._calculate_execution_stats()

    #     # Store execution data based on dict protocol
    #     if isinstance(exec_root, AsyncStateProtocol):
    #         await exec_root.set("execution_summary", value=stats)
    #     elif isinstance(exec_root, SyncStateProtocol):
    #         exec_root.set("execution_summary", value=stats)

    # async def start_span(self, operation, context):
    #     """
    #     Record the start of an operation execution.

    #     Args:
    #         operation: The operation that is starting
    #         context: The execution context
    #     """
    #     # Generate operation ID
    #     op_id = operation.key()

    #     # Register the operation if not already registered
    #     if op_id not in self._registered_operations:
    #         parent_op = None
    #         if hasattr(context, "parent") and context.parent:
    #             parent_op = context.parent.operation

    #         # Register operation in DAG
    #         root_op = operation
    #         while parent_op:
    #             root_op = parent_op
    #             parent_op = root_op.parent if hasattr(root_op, "parent") else None

    #         # Register the root operation
    #         await self.start_execution(root_op)

    #     # Record start time and basic information
    #     start_time = time.time()

    #     # Get parent operation ID if available
    #     parent_id = None
    #     if hasattr(context, "parent") and context.parent:
    #         parent_id = context.parent.operation.key()

    #     # Get operation metadata
    #     op_type = operation.__class__.__name__
    #     op_name = operation.metadata.name

    #     # Store span info in memory
    #     self._active_spans[op_id] = {
    #         "start_time": start_time,
    #         "op_type": op_type,
    #         "op_name": op_name,
    #         "status": "running",
    #         "parent_id": parent_id,
    #     }

    #     # Get the exec_dict based on state protocol
    #     exec_dict = None
    #     if isinstance(self.state, AsyncStateProtocol):
    #         exec_dict = await self.state.dict(*self._state_path, "execution")
    #     elif isinstance(self.state, SyncStateProtocol):
    #         exec_dict = self.state.dict(*self._state_path, "execution")
    #     else:
    #         # Unsupported state protocol
    #         return

    #     # Set execution data based on dict protocol
    #     if isinstance(exec_dict, AsyncStateProtocol):
    #         await exec_dict.set(op_id, value=self._active_spans[op_id])
    #     elif isinstance(exec_dict, SyncStateProtocol):
    #         exec_dict.set(op_id, value=self._active_spans[op_id])

    # async def end_span(self, operation, context, error=None):
    #     """
    #     Record the completion of an operation execution.

    #     Args:
    #         operation: The operation that completed
    #         context: The execution context
    #         error: Optional error that occurred during execution
    #     """
    #     # Generate operation ID
    #     op_id = operation.key()

    #     # Skip if the span wasn't started
    #     if op_id not in self._active_spans:
    #         return

    #     # Calculate execution time
    #     end_time = time.time()
    #     span_info = self._active_spans[op_id]
    #     duration = end_time - span_info["start_time"]

    #     # Update span info with completion data
    #     span_info["end_time"] = end_time
    #     span_info["duration"] = duration
    #     span_info["status"] = "error" if error else "completed"

    #     if error:
    #         span_info["error"] = str(error)
    #         span_info["error_type"] = error.__class__.__name__

    #     # Get dictionaries based on state protocol
    #     ops_dict = None
    #     exec_dict = None
    #     if isinstance(self.state, AsyncStateProtocol):
    #         ops_dict = await self.state.dict(*self._state_path, "operations")
    #         exec_dict = await self.state.dict(*self._state_path, "execution")
    #     elif isinstance(self.state, SyncStateProtocol):
    #         ops_dict = self.state.dict(*self._state_path, "operations")
    #         exec_dict = self.state.dict(*self._state_path, "execution")
    #     else:
    #         # Unsupported state protocol
    #         return

    #     # Store operation info based on dict protocol
    #     if isinstance(ops_dict, AsyncStateProtocol):
    #         await ops_dict.set(op_id, value=span_info)
    #     elif isinstance(ops_dict, SyncStateProtocol):
    #         ops_dict.set(op_id, value=span_info)

    #     # Remove from active execution based on dict protocol
    #     if isinstance(exec_dict, AsyncStateProtocol):
    #         await exec_dict.delete(op_id)
    #     elif isinstance(exec_dict, SyncStateProtocol):
    #         exec_dict.delete(op_id)

    #     # Remove from active spans
    #     try:
    #         del self._active_spans[op_id]
    #     except KeyError:
    #         pass

    # async def record_exception(self, operation, context, exception):
    #     """
    #     Record an exception that occurred during operation execution.

    #     Args:
    #         operation: The operation where the exception occurred
    #         context: The execution context
    #         exception: The exception that was raised
    #     """
    #     # Generate operation ID
    #     op_id = operation.key()

    #     # Skip if the span wasn't started
    #     if op_id not in self._active_spans:
    #         return

    #     # Update span info with error details
    #     self._active_spans[op_id]["status"] = "error"
    #     self._active_spans[op_id]["error"] = str(exception)
    #     self._active_spans[op_id]["error_type"] = exception.__class__.__name__

    #     # Get the exec_dict based on state protocol
    #     exec_dict = None
    #     if isinstance(self.state, AsyncStateProtocol):
    #         exec_dict = await self.state.dict(*self._state_path, "execution")
    #     elif isinstance(self.state, SyncStateProtocol):
    #         exec_dict = self.state.dict(*self._state_path, "execution")
    #     else:
    #         # Unsupported state protocol
    #         return

    #     # Update execution state based on dict protocol
    #     if isinstance(exec_dict, AsyncStateProtocol):
    #         await exec_dict.set(op_id, value=self._active_spans[op_id])
    #     elif isinstance(exec_dict, SyncStateProtocol):
    #         exec_dict.set(op_id, value=self._active_spans[op_id])

    # async def _calculate_execution_stats(self):
    #     """
    #     Calculate statistics about the workflow execution.

    #     Returns:
    #         Dict containing execution statistics
    #     """
    #     # Create default empty statistics
    #     default_stats = {
    #         "total": 0,
    #         "completed": 0,
    #         "failed": 0,
    #         "running": 0,
    #         "pending": 0,
    #         "timing": {
    #             "total": 0,
    #             "average": 0,
    #             "min": 0,
    #             "max": 0,
    #         },
    #     }

    #     # Get required dictionaries based on state protocol
    #     graph_dict = None
    #     ops_dict = None
    #     exec_dict = None

    #     if isinstance(self.state, AsyncStateProtocol):
    #         graph_dict = await self.state.dict(*self._state_path, "graph")
    #         ops_dict = await self.state.dict(*self._state_path, "operations")
    #         exec_dict = await self.state.dict(*self._state_path, "execution")
    #     elif isinstance(self.state, SyncStateProtocol):
    #         graph_dict = self.state.dict(*self._state_path, "graph")
    #         ops_dict = self.state.dict(*self._state_path, "operations")
    #         exec_dict = self.state.dict(*self._state_path, "execution")
    #     else:
    #         # Unsupported state protocol
    #         return default_stats

    #     # Get data from dictionaries based on their protocol
    #     graph_data = {}
    #     ops_data = {}
    #     exec_data = {}

    #     # Get graph data
    #     if isinstance(graph_dict, AsyncStateProtocol):
    #         graph_data = await graph_dict.to_dict()
    #     elif isinstance(graph_dict, SyncStateProtocol):
    #         graph_data = graph_dict.to_dict()
    #     else:
    #         return default_stats

    #     # Get operations data
    #     if isinstance(ops_dict, AsyncStateProtocol):
    #         ops_data = await ops_dict.to_dict()
    #     elif isinstance(ops_dict, SyncStateProtocol):
    #         ops_data = ops_dict.to_dict()
    #     else:
    #         return default_stats

    #     # Get execution data
    #     if isinstance(exec_dict, AsyncStateProtocol):
    #         exec_data = await exec_dict.to_dict()
    #     elif isinstance(exec_dict, SyncStateProtocol):
    #         exec_data = exec_dict.to_dict()
    #     else:
    #         return default_stats

    #     # Calculate statistics
    #     total_operations = len(graph_data)
    #     completed_operations = sum(1 for op in ops_data.values() if op.get("status") == "completed")
    #     failed_operations = sum(1 for op in ops_data.values() if op.get("status") == "error")
    #     running_operations = len(exec_data)
    #     pending_operations = (
    #         total_operations - completed_operations - failed_operations - running_operations
    #     )

    #     # Calculate timing statistics if available
    #     total_duration = 0
    #     min_duration = float("inf")
    #     max_duration = 0
    #     operation_durations = []

    #     for op in ops_data.values():
    #         if "duration" in op:
    #             duration = op["duration"]
    #             total_duration += duration
    #             min_duration = min(min_duration, duration)
    #             max_duration = max(max_duration, duration)
    #             operation_durations.append(duration)

    #     avg_duration = total_duration / len(operation_durations) if operation_durations else 0
    #     if min_duration == float("inf"):
    #         min_duration = 0

    #     return {
    #         "total": total_operations,
    #         "completed": completed_operations,
    #         "failed": failed_operations,
    #         "running": running_operations,
    #         "pending": pending_operations,
    #         "timing": {
    #             "total": total_duration,
    #             "average": avg_duration,
    #             "min": min_duration,
    #             "max": max_duration,
    #         },
    #     }


class TracingServiceSpec(Spec):
    """
    Specification for the TracingService.

    This specification defines the configuration and dependencies for the
    TracingService.
    """

    name: str = SpecField(default="tracing_service")
    factory: type = SpecField(default=TracingService)
    state: Spec = SpecField(default=StateSpec().with_value_at("storage", "path", value=".tracing"))
    state_root_path: tuple[str, ...] = SpecField(default=("_", "tracing"))
