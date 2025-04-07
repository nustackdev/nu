"""
Runtime context for operation execution.

This module defines the RuntimeContext class, which provides the execution context
for operations, including state access, metadata, and engine services.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Union

from .services import AsyncStateInterface, CancellationToken, ServiceRegistry, TracingService

__all__ = ["RuntimeContext"]


@dataclass(frozen=True)
class RuntimeContext:
    """Context for operation execution.

    Provides access to state, execution metadata, and engine services.
    This is the primary interface through which operations interact with
    their environment.

    Attributes:
        context_id: Unique identifier for this context instance
        state: Interface for accessing state
        operation_id: ID of the operation this context is for
        operation_path: Path to the operation in the execution tree
        parent_context_id: ID of the parent context, if any
        key: Key for the current item (for collection operations)
        index: Index for the current item (for collection operations)
        trace: Service for tracing execution events
        cancellation: Token for checking and propagating cancellation
        services: Registry of additional services available to operations
        data: Custom context data that can be used by operations
    """

    # Unique identifier for this context instance
    context_id: str

    # State access
    state: AsyncStateInterface

    # Execution tracking
    operation_id: str
    operation_path: List[str] = field(default_factory=list)

    # Execution metadata
    parent_context_id: Optional[str] = None
    key: Optional[Union[str, int]] = None
    index: Optional[int] = None

    # Engine services
    trace: TracingService = field(default_factory=TracingService)
    cancellation: CancellationToken = field(default_factory=CancellationToken)
    services: ServiceRegistry = field(default_factory=ServiceRegistry)

    # Custom context data
    data: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        state: AsyncStateInterface,
        operation_id: str,
        context_id: Optional[str] = None,
        parent_context_id: Optional[str] = None,
        operation_path: Optional[List[str]] = None,
        trace: Optional[TracingService] = None,
        cancellation: Optional[CancellationToken] = None,
        services: Optional[ServiceRegistry] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> RuntimeContext:
        """Create a new runtime context.

        This factory method provides a convenient way to create a new context
        with default values for optional parameters.

        Args:
            state: State interface for the context
            operation_id: ID of the operation this context is for
            context_id: Optional ID for the context (generated if not provided)
            parent_context_id: Optional ID of the parent context
            operation_path: Optional path to the operation in the execution tree
            trace: Optional tracing service
            cancellation: Optional cancellation token
            services: Optional service registry
            data: Optional custom context data

        Returns:
            A new RuntimeContext instance
        """
        return cls(
            context_id=context_id or str(uuid.uuid4()),
            state=state,
            operation_id=operation_id,
            operation_path=operation_path or [],
            parent_context_id=parent_context_id,
            trace=trace or TracingService(),
            cancellation=cancellation or CancellationToken(),
            services=services or ServiceRegistry(),
            data=data or {},
        )

    def derive(
        self,
        operation_id: Optional[str] = None,
        key: Optional[Union[str, int]] = None,
        index: Optional[int] = None,
        data_updates: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> RuntimeContext:
        """Create a new context derived from this one.

        This method creates a new context with the same properties as this one,
        but with specific fields updated. This is useful for creating contexts
        for child operations.

        Args:
            operation_id: Optional new operation ID
            key: Optional key for the derived context
            index: Optional index for the derived context
            data_updates: Optional updates to the context data
            **kwargs: Additional keyword arguments to update in the context

        Returns:
            A new context derived from this one with the specified updates
        """
        # Start with a copy of the current fields
        new_data = dict(self.data)

        # Apply data updates if provided
        if data_updates:
            new_data.update(data_updates)

        # Create the field updates
        updates = {
            # Fields that aren't explicitly overridden keep their current values
            "context_id": str(uuid.uuid4()),  # Always generate a new context ID
            "state": self.state,
            "operation_id": operation_id if operation_id is not None else self.operation_id,
            "operation_path": list(self.operation_path),  # Create a copy
            "parent_context_id": self.context_id,  # Current context becomes the parent
            "key": key if key is not None else self.key,
            "index": index if index is not None else self.index,
            "trace": self.trace,
            "cancellation": self.cancellation,
            "services": self.services,
            "data": new_data,
        }

        # Apply any additional kwargs
        updates.update(kwargs)

        # Create and return the new context
        return RuntimeContext(**updates)

    def with_operation_path(self, *path_components: str) -> RuntimeContext:
        """Create a derived context with an extended operation path.

        Args:
            *path_components: Components to append to the operation path

        Returns:
            A new context with the extended operation path
        """
        new_path = list(self.operation_path)
        new_path.extend(path_components)
        return self.derive(operation_path=new_path)

    async def trace_start(
        self, parent_operation_id: Optional[str] = None, details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Trace the start of an operation.

        Args:
            parent_operation_id: Optional ID of the parent operation
            details: Optional additional details for the trace event
        """
        await self.trace.operation_started(
            operation_id=self.operation_id,
            context_id=self.context_id,
            parent_operation_id=parent_operation_id or self.parent_context_id,
            details=details,
        )

    async def trace_complete(
        self, result: Any = None, details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Trace the successful completion of an operation.

        Args:
            result: Optional result of the operation
            details: Optional additional details for the trace event
        """
        await self.trace.operation_completed(
            operation_id=self.operation_id,
            context_id=self.context_id,
            result=result,
            parent_operation_id=self.parent_context_id,
            details=details,
        )

    async def trace_error(self, error: Exception, details: Optional[Dict[str, Any]] = None) -> None:
        """Trace an error in an operation.

        Args:
            error: The exception that occurred
            details: Optional additional details for the trace event
        """
        await self.trace.operation_failed(
            operation_id=self.operation_id,
            context_id=self.context_id,
            error=error,
            parent_operation_id=self.parent_context_id,
            details=details,
        )

    async def trace_cancel(self, details: Optional[Dict[str, Any]] = None) -> None:
        """Trace the cancellation of an operation.

        Args:
            details: Optional additional details for the trace event
        """
        await self.trace.operation_cancelled(
            operation_id=self.operation_id,
            context_id=self.context_id,
            parent_operation_id=self.parent_context_id,
            details=details,
        )

    async def trace_progress(
        self, progress: float, details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Trace progress in an operation.

        Args:
            progress: Progress value between 0.0 and 1.0
            details: Optional additional details for the trace event
        """
        await self.trace.operation_progress(
            operation_id=self.operation_id,
            context_id=self.context_id,
            progress=progress,
            parent_operation_id=self.parent_context_id,
            details=details,
        )

    async def trace_custom(self, event_name: str, details: Optional[Dict[str, Any]] = None) -> None:
        """Trace a custom event from an operation.

        Args:
            event_name: Name of the custom event
            details: Optional additional details for the trace event
        """
        await self.trace.custom_event(
            operation_id=self.operation_id,
            context_id=self.context_id,
            event_name=event_name,
            parent_operation_id=self.parent_context_id,
            details=details,
        )

    @property
    def is_cancelled(self) -> bool:
        """Check if cancellation has been requested for this context."""
        return self.cancellation.is_cancelled

    def register_cancellation_callback(self, callback: Callable[[], None]) -> Callable[[], None]:
        """Register a callback to be called when cancellation is requested.

        Args:
            callback: Function to call on cancellation

        Returns:
            A function that can be called to unregister the callback
        """
        return self.cancellation.register_callback(callback)

    def get_service(self, name: str) -> Any:
        """Get a service from the service registry.

        Args:
            name: Name of the service to get

        Returns:
            The service instance

        Raises:
            KeyError: If no service is registered with the given name
        """
        return self.services.get(name)

    def has_service(self, name: str) -> bool:
        """Check if a service is registered.

        Args:
            name: Name of the service to check

        Returns:
            True if a service is registered with the name, False otherwise
        """
        return self.services.has(name)
