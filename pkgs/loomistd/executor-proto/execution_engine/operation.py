"""
Operation interfaces and protocols.

This module defines the core abstractions for operations in the Loomi workflow system.
Operations are the building blocks of workflows, defining units of work to be executed.
"""

from __future__ import annotations

import abc
import uuid
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Protocol, Tuple, TypeVar, Union, runtime_checkable

__all__ = [
    "Operation",
    "ErrorBehavior",
    "OperationMetadata",
    "OperationResult",
    "PathComponent",
    "StatePath",
]


class ErrorBehavior(Enum):
    """Defines how operations should handle errors."""

    FAIL = auto()  # Stop execution and propagate error (default)
    CONTINUE = auto()  # Log error but continue execution
    RETRY = auto()  # Attempt to retry the failed operation


@dataclass(frozen=True)
class OperationMetadata:
    """Metadata for an operation.

    This class contains information about an operation that can be used
    for introspection, debugging, and visualization.

    Attributes:
        operation_type: The type of operation (e.g., "function", "sequence")
        description: Optional human-readable description of the operation
        custom_metadata: Optional additional metadata specific to the operation type
    """

    operation_type: str
    description: Optional[str] = None
    custom_metadata: Dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class Operation(Protocol):
    """Protocol defining the interface for all operations.

    Operations define units of work to be executed by the execution engine.
    They are primarily data structures that describe what to do, not how to do it.
    The actual execution is handled by the ExecutionEngine.
    """

    @property
    def id(self) -> str:
        """Get the operation's unique identifier."""
        ...

    @property
    def metadata(self) -> OperationMetadata:
        """Get the operation's metadata."""
        ...

    def get_children(self) -> List[Operation]:
        """Get all child operations of this operation.

        Returns:
            A list of child operations, or an empty list if none.
        """
        ...


class BaseOperation(abc.ABC):
    """Base abstract class implementing the Operation protocol.

    This class provides a common implementation for all operations,
    handling the operation ID and delegation to the execution engine.
    """

    def __init__(self, operation_id: Optional[str] = None):
        """Initialize the operation with an optional ID.

        Args:
            operation_id: Unique identifier for this operation instance.
                          If not provided, a UUID will be generated.
        """
        self._id = operation_id or str(uuid.uuid4())

    @property
    def id(self) -> str:
        """Get the operation's unique identifier."""
        return self._id

    @property
    @abc.abstractmethod
    def metadata(self) -> OperationMetadata:
        """Get the operation's metadata."""
        pass

    @abc.abstractmethod
    def get_children(self) -> List[Operation]:
        """Get all child operations of this operation.

        Returns:
            A list of child operations, or an empty list if none.
        """
        pass


# Type for state path components
PathComponent = Union[str, int]
StatePath = Tuple[PathComponent, ...]

# Result type for operations
T = TypeVar("T")
OperationResult = TypeVar("OperationResult")
