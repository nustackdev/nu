"""
Services for the operations framework.

This module defines the core services used by operations, including tracing,
cancellation, and state access.
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Protocol, Set, TypeVar

from .operation import StatePath

__all__ = [
    "CancellationToken",
    "TracingService",
    "AsyncStateInterface",
    "ServiceRegistry",
]

logger = logging.getLogger(__name__)

T = TypeVar("T")


class CancellationToken:
    """Token for tracking and propagating cancellation requests.

    A cancellation token allows operations to check if they have been
    cancelled and should stop execution.

    Attributes:
        is_cancelled: Whether cancellation has been requested
    """

    def __init__(self):
        """Initialize a new cancellation token."""
        self._cancelled = False
        self._cancelled_event = asyncio.Event()
        self._callbacks: Set[Callable[[], None]] = set()

    def cancel(self) -> None:
        """Signal cancellation to all listeners."""
        if not self._cancelled:
            self._cancelled = True
            self._cancelled_event.set()

            # Execute all registered callbacks
            for callback in self._callbacks:
                try:
                    callback()
                except Exception as e:
                    logger.error(f"Error in cancellation callback: {str(e)}")

    def register_callback(self, callback: Callable[[], None]) -> Callable[[], None]:
        """Register a callback to be called when cancellation is requested.

        Args:
            callback: Function to call on cancellation

        Returns:
            A function that can be called to unregister the callback
        """
        self._callbacks.add(callback)

        def unregister():
            self._callbacks.discard(callback)

        return unregister

    @property
    def is_cancelled(self) -> bool:
        """Check if cancellation has been requested."""
        return self._cancelled

    async def wait_for_cancellation(self) -> None:
        """Wait for cancellation to be requested."""
        await self._cancelled_event.wait()


class OperationEvent(Enum):
    """Types of events that can occur during operation execution."""

    STARTED = auto()  # Operation started execution
    COMPLETED = auto()  # Operation completed successfully
    FAILED = auto()  # Operation failed with an error
    CANCELLED = auto()  # Operation was cancelled
    RETRY = auto()  # Operation is being retried
    PROGRESS = auto()  # Operation reported progress
    CUSTOM = auto()  # Custom event type


@dataclass
class TraceEvent:
    """Event generated during operation execution.

    Attributes:
        event_type: Type of the event
        timestamp: Time the event was generated (seconds since epoch)
        operation_id: ID of the operation that generated the event
        context_id: ID of the execution context
        parent_operation_id: Optional ID of the parent operation
        details: Additional event details
    """

    event_type: OperationEvent
    timestamp: float
    operation_id: str
    context_id: str
    parent_operation_id: Optional[str] = None
    details: Dict[str, Any] | None = None


class TracingService:
    """Service for tracing operation execution.

    The tracing service records events during operation execution,
    providing visibility into what operations are doing and when.
    """

    def __init__(self):
        """Initialize the tracing service."""
        self._handlers: List[Callable[[TraceEvent], None]] = []

    def add_handler(self, handler: Callable[[TraceEvent], None]) -> Callable[[], None]:
        """Add a handler for trace events.

        Args:
            handler: Function that will be called with trace events

        Returns:
            A function that can be called to remove the handler
        """
        self._handlers.append(handler)

        def remove_handler():
            if handler in self._handlers:
                self._handlers.remove(handler)

        return remove_handler

    def _emit_event(self, event: TraceEvent) -> None:
        """Emit a trace event to all handlers.

        Args:
            event: The trace event to emit
        """
        for handler in self._handlers:
            try:
                handler(event)
            except Exception as e:
                # Log errors in handlers but don't let them propagate
                logger.error(f"Error in trace handler: {str(e)}")

    async def operation_started(
        self,
        operation_id: str,
        context_id: str,
        parent_operation_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Record that an operation has started.

        Args:
            operation_id: ID of the operation that started
            context_id: ID of the execution context
            parent_operation_id: Optional ID of the parent operation
            details: Additional event details
        """
        event = TraceEvent(
            event_type=OperationEvent.STARTED,
            timestamp=time.time(),
            operation_id=operation_id,
            context_id=context_id,
            parent_operation_id=parent_operation_id,
            details=details or {},
        )
        self._emit_event(event)

    async def operation_completed(
        self,
        operation_id: str,
        context_id: str,
        result: Any = None,
        parent_operation_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Record that an operation has completed successfully.

        Args:
            operation_id: ID of the operation that completed
            context_id: ID of the execution context
            result: Optional result of the operation
            parent_operation_id: Optional ID of the parent operation
            details: Additional event details
        """
        event_details = details or {}

        # Add the result to the details if provided
        if result is not None:
            # Try to safely serialize the result for the event
            try:
                result_str = str(result)
                if len(result_str) > 1000:
                    result_str = result_str[:1000] + "... (truncated)"
                event_details["result"] = result_str
            except Exception:
                event_details["result"] = "<unable to serialize result>"

        event = TraceEvent(
            event_type=OperationEvent.COMPLETED,
            timestamp=time.time(),
            operation_id=operation_id,
            context_id=context_id,
            parent_operation_id=parent_operation_id,
            details=event_details,
        )
        self._emit_event(event)

    async def operation_failed(
        self,
        operation_id: str,
        context_id: str,
        error: Exception,
        parent_operation_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Record that an operation has failed.

        Args:
            operation_id: ID of the operation that failed
            context_id: ID of the execution context
            error: The exception that caused the failure
            parent_operation_id: Optional ID of the parent operation
            details: Additional event details
        """
        event_details = details or {}
        event_details["error"] = str(error)
        event_details["error_type"] = type(error).__name__

        event = TraceEvent(
            event_type=OperationEvent.FAILED,
            timestamp=time.time(),
            operation_id=operation_id,
            context_id=context_id,
            parent_operation_id=parent_operation_id,
            details=event_details,
        )
        self._emit_event(event)

    async def operation_cancelled(
        self,
        operation_id: str,
        context_id: str,
        parent_operation_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Record that an operation was cancelled.

        Args:
            operation_id: ID of the operation that was cancelled
            context_id: ID of the execution context
            parent_operation_id: Optional ID of the parent operation
            details: Additional event details
        """
        event = TraceEvent(
            event_type=OperationEvent.CANCELLED,
            timestamp=time.time(),
            operation_id=operation_id,
            context_id=context_id,
            parent_operation_id=parent_operation_id,
            details=details or {},
        )
        self._emit_event(event)

    async def operation_progress(
        self,
        operation_id: str,
        context_id: str,
        progress: float,
        parent_operation_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Record progress in an operation.

        Args:
            operation_id: ID of the operation reporting progress
            context_id: ID of the execution context
            progress: Progress value between 0.0 and 1.0
            parent_operation_id: Optional ID of the parent operation
            details: Additional event details
        """
        event_details = details or {}
        event_details["progress"] = progress

        event = TraceEvent(
            event_type=OperationEvent.PROGRESS,
            timestamp=time.time(),
            operation_id=operation_id,
            context_id=context_id,
            parent_operation_id=parent_operation_id,
            details=event_details,
        )
        self._emit_event(event)

    async def custom_event(
        self,
        operation_id: str,
        context_id: str,
        event_name: str,
        parent_operation_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Record a custom event from an operation.

        Args:
            operation_id: ID of the operation emitting the event
            context_id: ID of the execution context
            event_name: Name of the custom event
            parent_operation_id: Optional ID of the parent operation
            details: Additional event details
        """
        event_details = details or {}
        event_details["event_name"] = event_name

        event = TraceEvent(
            event_type=OperationEvent.CUSTOM,
            timestamp=time.time(),
            operation_id=operation_id,
            context_id=context_id,
            parent_operation_id=parent_operation_id,
            details=event_details,
        )
        self._emit_event(event)


class AsyncStateInterface(Protocol):
    """Interface for accessing state asynchronously.

    This protocol defines the methods that must be implemented by any
    state provider used by operations.
    """

    async def get(self, path: StatePath, default: Any = None) -> Any:
        """Get a value from state at the specified path.

        Args:
            path: Path to the state value to get
            default: Value to return if the path doesn't exist

        Returns:
            The value at the specified path, or the default if not found
        """
        ...

    async def set(self, path: StatePath, value: Any) -> None:
        """Set a value in state at the specified path.

        Args:
            path: Path where the value should be stored
            value: Value to store
        """
        ...

    async def delete(self, path: StatePath) -> None:
        """Delete a value from state at the specified path.

        Args:
            path: Path to the state value to delete
        """
        ...

    async def exists(self, path: StatePath) -> bool:
        """Check if a value exists at the specified path.

        Args:
            path: Path to check

        Returns:
            True if a value exists at the path, False otherwise
        """
        ...


class ServiceRegistry:
    """Registry for operation services.

    The service registry provides a centralized way to register and
    retrieve services used by operations, such as tracing, state access,
    and more.
    """

    def __init__(self):
        """Initialize the service registry."""
        self._services: Dict[str, Any] = {}

    def register(self, name: str, service: Any) -> None:
        """Register a service.

        Args:
            name: Name to register the service under
            service: The service instance
        """
        self._services[name] = service

    def get(self, name: str) -> Any:
        """Get a registered service.

        Args:
            name: Name of the service to get

        Returns:
            The service instance

        Raises:
            KeyError: If no service is registered with the given name
        """
        if name not in self._services:
            raise KeyError(f"No service registered with name: {name}")
        return self._services[name]

    def has(self, name: str) -> bool:
        """Check if a service is registered.

        Args:
            name: Name of the service to check

        Returns:
            True if a service is registered with the name, False otherwise
        """
        return name in self._services
