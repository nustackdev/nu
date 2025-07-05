from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .composition_engine import CompositionEngine
    from .dependency_manager import DependencyManager
    from .manager import ResolutionManager
    from .resource_factory import ResourceFactory
    from .resource_registry import ResourceRegistry

__all__ = [
    "get_resolution_manager",
    "get_resource_registry",
    "get_dependency_manager",
    "get_resource_factory",
    "get_composition_engine",
]

# Global service instance
_resolution_manager: "ResolutionManager | None" = None


def get_resolution_manager() -> "ResolutionManager":
    """
    Get the global resolution manager instance.

    This function initializes the resolution manager if it hasn't been created yet.
    It ensures that there is a single instance of the resolution manager throughout
    the application lifecycle.
    """
    from .manager import ResolutionManager

    global _resolution_manager
    if _resolution_manager is None:
        _resolution_manager = ResolutionManager()
    return _resolution_manager


def get_resource_registry() -> "ResourceRegistry":
    """
    Get the global resource registry.

    Returns:
        ResourceRegistry from the global resolution manager
    """
    return get_resolution_manager().resource_registry


def get_dependency_manager() -> "DependencyManager":
    """
    Get the global dependency manager.

    Returns:
        DependencyManager from the global resolution manager
    """
    return get_resolution_manager().dependency_manager


def get_resource_factory() -> "ResourceFactory":
    """
    Get the global resource factory.

    Returns:
        ResourceFactory from the global resolution manager
    """
    return get_resolution_manager().resource_factory


def get_composition_engine() -> "CompositionEngine":
    """
    Get the global composition engine.

    Returns:
        CompositionEngine from the global resolution manager
    """
    return get_resolution_manager().composition_engine
