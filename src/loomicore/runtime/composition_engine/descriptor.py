from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, TypeVar

from loomicore.common.descriptor import BaseDescriptor

if TYPE_CHECKING:
    from loomicore.resource import Resource
    from loomicore.runtime.dependency_manager import DependencyManager


__all__ = [
    "BaseResourceDescriptor",
]


ResourceType = TypeVar("ResourceType", bound="Resource")


class BaseResourceDescriptor(BaseDescriptor[ResourceType], ABC):
    """Base descriptor for service dependencies with protocol validation."""

    @abstractmethod
    def resolve(
        self, parent: "Resource", name: str, dependency_manager: "DependencyManager"
    ) -> "Resource":
        """Resolve this descriptor to its actual value."""
        raise NotImplementedError("resolve() must be implemented by subclasses")
