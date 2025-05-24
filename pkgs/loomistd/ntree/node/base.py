"""
Node implementation for the state management system.

This module defines the abstract Node class, which serves as the base
for all nodes in the state tree.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import ClassVar

import attrs

from ..path import DataPath
from ..transaction import TransactionalBase
from ..types import Empty, NodeType

__all__ = [
    "BaseNode",
]


@attrs.define(frozen=True, kw_only=True)
class BaseNode(TransactionalBase, ABC):
    """
    Abstract base class for all nodes in the state tree.

    Nodes are the building blocks of the state tree and come in two types:
    - Container nodes: Can contain other nodes (like directories)
    - Primitive nodes: Contain a single value (like files)

    Nodes can be used as context managers for transaction handling:

    Example:
        ```python
        with node as n:
            # Operations on node with transaction
            value = n.some_operation()
        # Transaction automatically committed
        ```
    """

    # Path to this node in the state tree
    path: DataPath = attrs.field(eq=False, kw_only=True)

    # Empty marker for non-existent values
    EMPTY: ClassVar[Empty] = Empty()

    # Markers for node types
    TYPE_FIELD_SUFFIX: ClassVar[str] = "T"

    @property
    @abstractmethod
    def node_type(self) -> NodeType:
        """
        Get the type of this node.

        Returns:
            NodeType: CONTAINER or PRIMITIVE
        """
        pass
