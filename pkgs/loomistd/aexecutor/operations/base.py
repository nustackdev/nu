"""
Base class for all operation nodes.

This module provides the Operation class, which all operations
should inherit from to ensure consistent behavior.
"""

from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING, Generic

from loomi.evaluator.interface.operations import OperationProtocol
from loomi.evaluator.interface.types import ErrorBehavior
from loomi.state.interface.type_vars import StateT

from .metadata import OperationMetadata
from .node import DAGNodeMixin

if TYPE_CHECKING:
    from ..context.context import Context


class Operation(ABC, DAGNodeMixin["Operation"], Generic[StateT]):
    """
    Base class for all operations.

    Implements common functionality for operations, including error handling,
    logging, and tracing. All operations should inherit from this class.

    Args:
        error_behavior: How to handle errors that occur during execution
        on_fail: Operation to execute when an error occurs
    """

    def __init__(
        self,
        *,
        error_behavior: ErrorBehavior = "fail",
        on_fail: Operation | None = None,
    ):
        """
        Initialize the operation.

        Args:
            error_behavior: How to handle errors that occur during execution
            on_fail: Operation to execute when an error occurs
        """
        super().__init__()

        if error_behavior not in ("fail", "continue"):
            raise ValueError(f"Invalid error_behavior: {error_behavior}")

        self._error_behavior = error_behavior
        self._on_fail = on_fail

    @property
    def metadata(self) -> OperationMetadata:
        """
        Get the operation's metadata.

        The metadata includes the operation's name, description, and any
        custom properties. By default, the name is the class name and
        the description is the class docstring.

        Returns:
            The operation metadata
        """
        return OperationMetadata(
            name=self.__class__.__name__,
            description=self.__doc__ or "",
            custom_properties={},
        )

    def __repr__(self):
        """Return a string representation of the operation."""
        return (
            f"{self.__class__.__name__}("
            f"error_behavior={self._error_behavior}, "
            f"on_fail={self._on_fail})"
        )


if TYPE_CHECKING:
    _: type[OperationProtocol[Operation, "Context"]] = Operation
