"""
Resource Runtime - Centralized runtime system for resource management.

This module provides the core resource runtime that orchestrates all live resource
operations, dependency coordination, and lifecycle management during program execution.
"""

from __future__ import annotations

from .composition_engine import CompositionEngine
from .dependency_manager import DependencyManager
from .lifecycle_manager import LifecycleManager
from .resource_factory import ResourceFactory
from .resource_registry import ResourceRegistry

__all__ = [
    "ResourceRuntime",
]


class ResourceRuntime:
    """
    Centralized runtime system for live resource management.

    This runtime orchestrates:
    - Live resource creation and deduplication during execution
    - Active dependency coordination and relationship management
    - Dynamic resource composition with attach descriptors
    - Centralized lifecycle and state management
    - TODO: Thread-safe runtime operations

    The runtime acts as the executing system that manages all live resource
    operations, allowing user-facing classes to remain thin and focused.

    Architecture:
        - ResourceRegistry: Instance tracking and deduplication
        - DependencyManager: Relationship management
        - CompositionEngine: Attach descriptor resolution
        - LifecycleManager: State and lifecycle operations (NEW)
        - ResourceFactory: Instance creation
    """

    def __init__(self) -> None:
        """Initialize the resource runtime with its operational components."""
        # Core instance tracking
        self._resource_registry: ResourceRegistry = ResourceRegistry()

        # Relationship management
        self._dependency_manager: DependencyManager = DependencyManager(self._resource_registry)

        # Attach descriptor resolution
        self._composition_engine: CompositionEngine = CompositionEngine(self._dependency_manager)

        # Centralized lifecycle and state management
        self._lifecycle_manager: LifecycleManager = LifecycleManager(
            self._dependency_manager, self._composition_engine
        )

        # Instance creation
        self._resource_factory: ResourceFactory = ResourceFactory(
            self._resource_registry, self._dependency_manager, self._lifecycle_manager
        )

    # === Component Access ===

    @property
    def resource_registry(self) -> "ResourceRegistry":
        """Get the resource registry for live instance tracking."""
        return self._resource_registry

    @property
    def dependency_manager(self) -> "DependencyManager":
        """Get the dependency manager for active relationship coordination."""
        return self._dependency_manager

    @property
    def resource_factory(self) -> "ResourceFactory":
        """Get the resource factory for runtime instance creation."""
        return self._resource_factory

    @property
    def composition_engine(self) -> "CompositionEngine":
        """Get the composition engine for dynamic resource assembly."""
        return self._composition_engine

    @property
    def lifecycle_manager(self) -> "LifecycleManager":
        """Get the lifecycle manager for state and lifecycle operations."""
        return self._lifecycle_manager
