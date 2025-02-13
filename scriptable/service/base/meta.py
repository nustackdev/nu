"""
Service metaclass implementation.

This module provides the ServiceMeta metaclass which handles service instantiation,
feature registration, and lifecycle management. The metaclass coordinates with
the dependency and registry systems to ensure proper service creation and tracking.

Key Features:
- Service instance management and deduplication
- Feature registration via declarative properties
- Context-aware instantiation
- Thread-safe service creation
- Proper dependency and registry coordination

Example Usage:
    class MyService(BaseService, metaclass=ServiceMeta, special_feature=Feature()):
        def __init__(self, spec):
            super().__init__(spec)
            # Service now has self.special_feature property
"""

from __future__ import annotations

from abc import ABCMeta
from threading import Lock
from typing import TYPE_CHECKING, Any, ClassVar, Dict, Generic, TypeVar, cast

from scriptable.service.lib.dependency_manager import DependencyManager
from scriptable.service.lib.service_registry import ServiceRegistry

from .exceptions import CreationError, ServiceError
from .logger import logger
from .spec import Spec

if TYPE_CHECKING:
    from .bases import Service

__all__ = [
    "ServiceMeta",
]

# Type variables for generic service and feature types
ServiceT = TypeVar("ServiceT", bound="Service")
FeatureT = TypeVar("FeatureT")


class ServiceMeta(ABCMeta, Generic[ServiceT]):
    """
    Metaclass for service classes.

    This metaclass handles:
    - Service instance creation and deduplication
    - Feature registration and property creation
    - Integration with dependency and registry systems
    - Context-aware service instantiation

    The metaclass ensures services are properly registered and tracked
    throughout their lifecycle, whether created directly or as dependencies.

    Features:
    - Declarative feature registration via class properties
    - Context-preserving service instantiation
    - Thread-safe instance management
    - Integration with dependency tracking system

    Example:
        class MyService(BaseService, metaclass=ServiceMeta):
            # Features automatically become properties
            cache = CacheFeature()
            storage = StorageFeature()
    """

    # Shared managers as class variables
    _registry: ClassVar[ServiceRegistry] = ServiceRegistry()
    _dep_manager: ClassVar[DependencyManager] = DependencyManager(_registry)

    # Lock for thread-safe instance creation
    _creation_lock: ClassVar[Lock] = Lock()

    def __new__(
        mcs,
        name: str,
        bases: tuple[type, ...],
        namespace: Dict[str, Any],
        **features: Any,
    ) -> type[ServiceT]:
        """
        Create new service class with registered features.

        This method handles:
        - Feature registration and property creation
        - Manager references injection
        - Class creation and initialization

        Args:
            name: Class name
            bases: Base classes
            namespace: Class namespace
            **features: Service features to register

        Returns:
            Created service class with registered features

        Example:
            class MyService(BaseService, metaclass=ServiceMeta,
                          cache=CacheFeature()):
                pass
            # Creates service class with cache property
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

        logger.info(f"Created service class: '{name}'")

        # Create class with features
        cls = cast(type[ServiceT], super().__new__(mcs, name, bases, namespace))
        return cls

    def __call__(
        cls: type[ServiceT],  # type: ignore
        spec: Spec | None = None,
        /,
        *args: Any,
        **kwargs: Any,
    ) -> ServiceT:
        """
        Create or get existing service instance.

        This method handles:
        - Service deduplication via registry
        - Context-aware instance creation
        - Proper dependency registration
        - Thread-safe service instantiation

        The method preserves the creation context (root vs dependency)
        throughout the service's lifecycle for proper cleanup handling.

        Args:
            spec: Service specification (optional)
            *args: Additional constructor arguments
            **kwargs: Additional constructor keywords

        Returns:
            New or existing service instance

        Raises:
            CreationError: If service creation fails
            ServiceError: For other service-related errors

        Example:
            # Create root service
            service = MyService(spec)

            # Create as dependency
            service = MyService(spec, __is_dependency__=True)
        """
        try:
            with cls._creation_lock:  # type: ignore
                # Use empty spec if none provided
                if spec is None:
                    spec = Spec(factory=cls)

                if spec.factory is None:
                    spec.factory = cls

                # Extract creation context
                is_dependency = kwargs.pop("__is_dependency__", False)

                # Try get existing instance
                instance = cls._registry.get_service(spec)
                if instance is not None:
                    logger.info(f"Reusing existing service instance: '{instance.readable_name}'")
                    # Update dependency tracking
                    cls._dep_manager.register_service(instance, is_dependency=is_dependency)
                    return cast(ServiceT, instance)

                logger.debug(f"Creating new service instance: '{cls.factory_name()}'")
                try:
                    # Create new instance
                    instance = super().__call__(spec, *args, **kwargs)
                except Exception as e:
                    raise CreationError(f"Failed to instantiate '{cls.factory_name()}'") from e

                # Register with proper context
                cls._registry.add_service(instance)
                cls._dep_manager.register_service(instance, is_dependency=is_dependency)

                logger.info(f"Created service instance: '{instance.readable_name}'")
                return cast(ServiceT, instance)

        except (CreationError, ServiceError):
            raise
        except Exception as e:
            logger.error(f"Unexpected error creating service: {str(e)}")
            raise ServiceError(f"Failed to create service '{cls.factory_name()}'") from e

    @property
    def registry(cls) -> ServiceRegistry:
        """
        Get service registry instance.

        Returns:
            Shared service registry
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


__all__ = [
    "ServiceMeta",
]
