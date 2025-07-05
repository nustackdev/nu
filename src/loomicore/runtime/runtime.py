"""
Resource Runtime - Centralized runtime system for resource management.

This module provides the core resource runtime that orchestrates all live resource
operations, dependency coordination, and lifecycle management during program execution.
"""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING, Generic, TypeVar

from .composition_engine import CompositionEngine
from .dependency_manager import DependencyManager
from .resource_factory import ResourceFactory
from .resource_registry import ResourceRegistry

if TYPE_CHECKING:
    from loomicore.resource import Resource

__all__ = [
    "ResourceRuntime",
]

ResourceT = TypeVar("ResourceT", bound="Resource")


class ResourceRuntime(Generic[ResourceT]):
    """
    Centralized runtime system for live resource management.

    This runtime orchestrates:
    - Live resource creation and deduplication during execution
    - Active dependency coordination and relationship management
    - Dynamic resource composition with attach descriptors
    - Thread-safe runtime operations

    The runtime acts as the executing system that manages all live resource
    operations, allowing user-facing classes to remain thin and focused.
    """

    def __init__(self) -> None:
        """Initialize the resource runtime with its operational components."""
        self._resource_registry: ResourceRegistry[ResourceT] = ResourceRegistry()
        self._dependency_manager: DependencyManager[ResourceT] = DependencyManager(
            self._resource_registry
        )
        self._resource_factory: ResourceFactory[ResourceT] = ResourceFactory(
            self._resource_registry, self._dependency_manager
        )
        self._composition_engine: CompositionEngine[ResourceT] = CompositionEngine(
            self._dependency_manager
        )
        self._lock = threading.Lock()

    @property
    def resource_registry(self) -> "ResourceRegistry[ResourceT]":
        """Get the resource registry for live instance tracking."""
        return self._resource_registry

    @property
    def dependency_manager(self) -> "DependencyManager[ResourceT]":
        """Get the dependency manager for active relationship coordination."""
        return self._dependency_manager

    @property
    def resource_factory(self) -> "ResourceFactory[ResourceT]":
        """Get the resource factory for runtime instance creation."""
        return self._resource_factory

    @property
    def composition_engine(self) -> "CompositionEngine[ResourceT]":
        """Get the composition engine for dynamic resource assembly."""
        return self._composition_engine
