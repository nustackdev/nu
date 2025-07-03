"""
Resource metaclass implementation.

This module provides the ResourceMeta metaclass which handles resource instantiation,
feature registration, and lifecycle management. The metaclass coordinates with
the dependency and registry systems to ensure proper resource creation and tracking.

Key Features:
- Resource instance management and deduplication
- Feature registration via declarative properties
- Context-aware instantiation
- Thread-safe resource creation
- Proper dependency and registry coordination
- Remote resource support
"""

from __future__ import annotations

from abc import ABCMeta
from threading import Lock
from typing import TYPE_CHECKING, Any, ClassVar, Generic, TypeVar, cast

from ..dependency_manager import DependencyManager
from ..exceptions import CreationError, ResourceError
from ..registry import ResourceRegistry
from ..spec import Spec
from .logger import logger

if TYPE_CHECKING:
    from .resource import AsyncResource, SyncResource

__all__ = [
    "ResourceMeta",
]

# Type variables for generic resource and feature types
ResourceT = TypeVar("ResourceT", bound="AsyncResource | SyncResource")
FeatureT = TypeVar("FeatureT")


class ResourceMeta(ABCMeta, Generic[ResourceT]):
    """
    Metaclass for resource classes.

    This metaclass handles:
    - Resource instance creation and deduplication
    - Feature registration and property creation
    - Integration with dependency and registry systems
    - Context-aware resource instantiation

    The metaclass ensures resources are properly registered and tracked
    throughout their lifecycle, whether created directly or as dependencies.

    Features:
    - Declarative feature registration via class properties
    - Context-preserving resource instantiation
    - Thread-safe instance management
    - Integration with dependency tracking system

    Example:
        class MyResource(BaseResource, metaclass=ResourceMeta):
            # Features automatically become properties
            cache = CacheFeature()
            storage = StorageFeature()
    """

    # Shared managers as class variables
    _registry: ClassVar[ResourceRegistry] = ResourceRegistry()
    _dep_manager: ClassVar[DependencyManager] = DependencyManager(_registry)

    # Lock for thread-safe instance creation
    _creation_lock: ClassVar[Lock] = Lock()

    def __new__(
        mcs,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, Any],
    ) -> type[ResourceT]:
        """
        Create new resource class with registered features.

        This method handles:
        - Feature registration and property creation
        - Manager references injection
        - Class creation and initialization

        Args:
            name: Class name
            bases: Base classes
            namespace: Class namespace
            **features: Resource features to register

        Returns:
            Created resource class with registered features

        Example:
            class MyResource(BaseResource, metaclass=ResourceMeta,
                          cache=CacheFeature()):
                pass
            # Creates resource class with cache property
        """
        # Register feature properties
        # for feature_name, feature in features.items():
        #     # Create private storage name
        #     storage_name = f"_{feature_name}_"

        #     # Create property accessor with proper closure
        #     def make_getter(name: str) -> property:
        #         """Create getter for feature property."""

        #         def getter(self: Any) -> Any:
        #             return getattr(self, name, None)

        #         return property(getter)

        #     # Add to namespace
        #     namespace[storage_name] = feature
        #     namespace[feature_name] = make_getter(storage_name)

        # Store manager references
        namespace["_registry"] = mcs._registry
        namespace["_dep_manager"] = mcs._dep_manager

        logger.info(f"Created resource class: '{name}'")

        # Create class with features
        cls = cast(type[ResourceT], super().__new__(mcs, name, bases, namespace))
        return cls

    def __call__(
        cls: type[ResourceT],  # type: ignore
        spec: Spec | None = None,
        /,
        *args: Any,
        **kwargs: Any,
    ) -> ResourceT:
        """
        Create or get existing resource instance.

        This method handles:
        - Resource deduplication via registry
        - Context-aware instance creation
        - Proper dependency registration
        - Thread-safe resource instantiation

        The method preserves the creation context (root vs dependency)
        throughout the resource's lifecycle for proper cleanup handling.

        Args:
            spec: Resource specification (optional)
            *args: Additional constructor arguments
            **kwargs: Additional constructor keywords

        Returns:
            New or existing resource instance

        Raises:
            CreationError: If resource creation fails
            ResourceError: For other resource-related errors

        Example:
            # Create root resource
            resource = MyResource(spec)

            # Create as dependency
            resource = MyResource(spec, __is_dependency__=True)
        """
        try:
            # with cls._creation_lock:  # type: ignore
            # Use empty spec if none provided
            if spec is None:
                spec = Spec(factory=cls)

            if spec.factory is None:
                spec.factory = cls

            # Extract creation context
            is_dependency = kwargs.pop("__is_dependency__", False)

            # Check if this is a remote resource request
            if spec.is_remote():
                return cls._get_or_create_remote_resource(spec, is_dependency)

            # Try get existing instance
            instance = cls._registry.get_resource(spec)
            if instance is not None:
                logger.info(f"Reusing existing resource instance: '{instance.readable_name}'")
                # Update dependency tracking
                cls._dep_manager.register_resource(instance, is_dependency=is_dependency)
                return cast(ResourceT, instance)

            logger.debug(f"Creating new resource instance: '{cls.factory_name()}'")
            try:
                # Create new instance
                instance = super().__call__(spec, *args, **kwargs)
            except Exception as e:
                raise CreationError(f"Failed to instantiate '{cls.factory_name()}'") from e

            # Register with proper context
            cls._registry.add_resource(instance)
            cls._dep_manager.register_resource(instance, is_dependency=is_dependency)

            logger.info(f"Created resource instance: '{instance.readable_name}'")
            return cast(ResourceT, instance)

        except (CreationError, ResourceError):
            raise
        except Exception as e:
            logger.error(f"Unexpected error creating resource: {str(e)}")
            raise ResourceError(f"Failed to create resource '{cls.factory_name()}'") from e

    @property
    def registry(cls) -> ResourceRegistry:
        """
        Get resource registry instance.

        Returns:
            Shared resource registry
        """
        return cls._registry

    @property
    def dep_manager(cls) -> DependencyManager:
        """
        Get dependency manager instance.

        Returns:
            Shared dependency manager
        """
        return cls._dep_manager

    @classmethod
    def _get_or_create_remote_resource(cls, spec: Spec, is_dependency: bool) -> Any:
        """
        Create a remote resource using RemoteResourceProxy.

        Args:
            spec: Remote resource specification
            is_dependency: Whether resource is being created as dependency

        Returns:
            RemoteResourceProxy instance
        """
        from ..coordinators.remote import create_remote_resource_proxy

        proxy = create_remote_resource_proxy(spec)

        return proxy
