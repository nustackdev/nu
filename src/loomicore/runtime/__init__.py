from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .composition_engine import CompositionEngine
    from .dependency_manager import DependencyManager
    from .resource_factory import ResourceFactory
    from .resource_registry import ResourceRegistry
    from .runtime import ResourceRuntime

__all__ = [
    "get_resource_runtime",
    "get_resource_registry",
    "get_dependency_manager",
    "get_resource_factory",
    "get_composition_engine",
]

# Global runtime instance
_resource_runtime: "ResourceRuntime | None" = None


def get_resource_runtime() -> "ResourceRuntime":
    """
    Get the global resource runtime instance.

    This function initializes the resource runtime if it hasn't been created yet.
    It ensures that there is a single runtime instance throughout the application
    lifecycle for managing all live resource operations.
    """
    from .runtime import ResourceRuntime

    global _resource_runtime
    if _resource_runtime is None:
        _resource_runtime = ResourceRuntime()
    return _resource_runtime


def get_resource_registry() -> "ResourceRegistry":
    """
    Get the global resource registry for live instance tracking.

    Returns:
        ResourceRegistry from the global resource runtime
    """
    return get_resource_runtime().resource_registry


def get_dependency_manager() -> "DependencyManager":
    """
    Get the global dependency manager for active relationship coordination.

    Returns:
        DependencyManager from the global resource runtime
    """
    return get_resource_runtime().dependency_manager


def get_resource_factory() -> "ResourceFactory":
    """
    Get the global resource factory for runtime instance creation.

    Returns:
        ResourceFactory from the global resource runtime
    """
    return get_resource_runtime().resource_factory


def get_composition_engine() -> "CompositionEngine":
    """
    Get the global composition engine for dynamic resource assembly.

    Returns:
        CompositionEngine from the global resource runtime
    """
    return get_resource_runtime().composition_engine
