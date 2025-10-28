"""Node implementation for the state management system.

This module defines the abstract Node class, which serves as the base
for all nodes in the state tree.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from functools import cached_property
from typing import TYPE_CHECKING, ClassVar

import attrs

from redwood.abc import EMPTY, Empty, TupleKey

from ..context import ContextualBase


if TYPE_CHECKING:
    from redwood.be import StorageContextType
    from redwood.storage import ReactiveStorage

    from ..types import NodeType


__all__ = [
    "BaseNode",
]


@attrs.define(frozen=True, kw_only=True)
class BaseNode(ContextualBase, ABC):
    """Abstract base class for all nodes in the state tree.

    Nodes are the building blocks of the state tree and come in two types:
    - Container nodes: Can contain other nodes (like directories)
    - Primitive nodes: Contain a single value (like files)

    Nodes support both transaction and snapshot contexts for unified operations:
    """

    # Backend instance for transaction management
    backend: ReactiveStorage = attrs.field(kw_only=True)

    # Current transaction if any
    ctx: StorageContextType = attrs.field(kw_only=True)  # type: ignore[assignment]

    # Path to this node in the state tree
    path: TupleKey = attrs.field(eq=False, kw_only=True)

    # Empty marker for non-existent values
    EMPTY: ClassVar[Empty] = EMPTY

    # Markers for node types
    TYPE_FIELD_SUFFIX: ClassVar[str] = "T"

    @cached_property
    @abstractmethod
    def node_type(self) -> NodeType:
        """Get the type of this node.

        Returns:
            NodeType: CONTAINER or PRIMITIVE
        """
        pass
