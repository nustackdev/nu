"""
Node implementation for the state management system.

This module defines the abstract Node class, which serves as the base
for all nodes in the state tree.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import ClassVar

import attrs

from ..backend import BackendProtocol, TransactionProtocol
from ..path import Path
from ..types import EMPTY, Empty, NodeType

__all__ = [
    "BaseNode",
]


@attrs.define(frozen=True, kw_only=True)
class BaseNode(ABC):
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

    # Backend instance for transaction management
    backend: BackendProtocol = attrs.field(kw_only=True)

    # Current transaction if any
    tx: TransactionProtocol = attrs.field(kw_only=True)

    # Path to this node in the state tree
    path: Path = attrs.field(eq=False, kw_only=True)

    # Empty marker for non-existent values
    EMPTY: ClassVar[Empty] = EMPTY

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
