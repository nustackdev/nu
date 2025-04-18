"""
Base class for all operation nodes.

This module provides the Operation class, which all operations
should inherit from to ensure consistent behavior.
"""

from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING, Generic

from anytree import NodeMixin

from loomi.interfaces.executor.operations import OperationProtocol
from loomi.interfaces.executor.types import ErrorBehavior
from loomi.interfaces.state.type_vars import StateDictT

from .metadata import OperationMetadata

if TYPE_CHECKING:
    from ..context.context import Context


class Operation(ABC, NodeMixin, Generic[StateDictT]):
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
        if error_behavior not in ("fail", "continue"):
            raise ValueError(f"Invalid error_behavior: {error_behavior}")

        self._error_behavior = error_behavior
        self._on_fail = on_fail

    @property
    def structural_path(self) -> tuple[str, ...]:
        """
        Get the structural path of the operation.

        The structural path is a tuple representing the position of the
        operation in the operation tree.

        Returns:
            The structural path
        """
        parent_path = self.parent.structural_path if self.parent else tuple()
        return parent_path + (self.__class__.__name__,)

    @property
    def structural_path_str(self) -> str:
        """
        Get the structural path of the operation as a string.

        Returns:
            The structural path as a string
        """
        return ".".join(self.structural_path)

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

    @property
    def children(self) -> tuple[Operation, ...]:
        """
        Get the child operations.

        Returns:
            The child operations
        """
        return tuple(NodeMixin.children.fget(self))  # type: ignore

    @children.setter
    def children(self, children: tuple[Operation, ...]) -> None:
        """
        Set the child operations.

        Args:
            children: The child operations to set
        """
        NodeMixin.children.fset(self, children)  # type: ignore

    @children.deleter
    def children(self) -> None:
        NodeMixin.children.fdel(self)  # type: ignore

    @property
    def parent(self) -> Operation | None:
        """
        Get the parent operation.

        Returns:
            The parent operation, or None if this is the root operation
        """
        return NodeMixin.parent.fget(self)  # type: ignore

    @parent.setter
    def parent(self, parent: Operation | None) -> None:
        """
        Set the parent operation.

        Args:
            parent: The parent operation to set
        """
        NodeMixin.parent.fset(self, parent)  # type: ignore

    @parent.deleter
    def parent(self) -> None:
        NodeMixin.parent.fdel(self)  # type: ignore


if TYPE_CHECKING:
    _: type[OperationProtocol[Operation, "Context"]] = Operation
