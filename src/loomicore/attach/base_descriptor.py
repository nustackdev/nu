"""
Core descriptor base class for attach patterns.

This module provides the BaseResourceDescriptor that all attach patterns
inherit from. It defines the self-resolution interface that enables the
composition engine to work with any descriptor type without pattern-specific logic.
"""

from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, Any, TypeVar

from loomicore.common.descriptor import BaseDescriptor

if TYPE_CHECKING:
    from loomicore.resource import Resource
    from loomicore.runtime.dependency_manager import DependencyManager

__all__ = [
    "BaseResourceDescriptor",
]

ResourceType = TypeVar("ResourceType", bound="Resource")


class BaseResourceDescriptor(BaseDescriptor[ResourceType]):
    """
    Base descriptor for all attach patterns with self-resolution capability.

    This class provides the foundation for all attach descriptors by defining
    the self-resolution interface. Each descriptor type implements its own
    resolve() method to handle pattern-specific logic.

    The self-resolution approach eliminates the need for pattern-specific
    conditional logic in the composition engine, making the system easily
    extensible for new attach patterns.
    """

    @abstractmethod
    def resolve(
        self, parent: "Resource", name: str, dependency_manager: "DependencyManager"
    ) -> Any:
        """
        Resolve this descriptor to its actual value.

        This method is called by the CompositionEngine during resource
        composition to convert the descriptor into its runtime value.
        Different descriptor types return different values:

        - Attach(): Returns Resource instance
        - AttachMany(): Returns ListCoordinator
        - AttachManyDict(): Returns DictCoordinator

        Args:
            parent: The resource that contains this descriptor
            name: The attribute name of this descriptor on the parent
            dependency_manager: Dependency manager for resource operations

        Returns:
            The resolved value (type depends on descriptor pattern)

        Raises:
            DependencyError: If resolution fails for any reason

        Notes:
            - Called during resource composition
            - Must handle all pattern-specific logic internally
            - Should use dependency_manager for resource creation/tracking
            - Return type varies by pattern (Resource, Coordinator, etc.)
        """
        raise NotImplementedError
