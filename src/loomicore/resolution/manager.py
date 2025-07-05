"""
Resolution Service - Centralized resource resolution and composition.

This module provides the core resolution service that orchestrates all resource
creation, dependency management, and lifecycle coordination.
"""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING, Generic, TypeVar

from .dependency_manager import DependencyManager
from .resource_registry import ResourceRegistry

if TYPE_CHECKING:
    from loomicore.resource import Resource

__all__ = [
    "ResolutionManager",
]

ResourceT = TypeVar("ResourceT", bound="Resource")


class ResolutionManager(Generic[ResourceT]):
    """
    Centralized service for resource resolution and composition.

    This service orchestrates:
    - Resource creation and deduplication via registry
    - Dependency resolution and relationship management
    - Resource composition with attach descriptors
    - Thread-safe resource operations

    The service acts as the single point of coordination for all resource
    operations, allowing user-facing classes to remain thin and focused.
    """

    def __init__(self) -> None:
        """Initialize the resolution service with its components."""
        self._registry: ResourceRegistry[ResourceT] = ResourceRegistry()
        self._dependency_manager: DependencyManager[ResourceT] = DependencyManager(self._registry)
        self._lock = threading.Lock()

    @property
    def registry(self) -> "ResourceRegistry[ResourceT]":
        """Get the resource registry."""
        return self._registry

    @property
    def dependency_manager(self) -> "DependencyManager[ResourceT]":
        """Get the dependency manager."""
        return self._dependency_manager
