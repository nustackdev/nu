"""
Resource Factory - Handles resource creation and instantiation logic.

This module provides the ResourceFactory which encapsulates all resource creation logic
that was previously handled in the ResourceMeta metaclass. It manages resource
instantiation, deduplication, context tracking, and error handling.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from loomicore.spec import ProxySpec, Spec

from .exceptions import CreationError, ResourceError
from .logger import logger

if TYPE_CHECKING:
    from loomicore.resource import Resource

    from ..dependency_manager import DependencyManager
    from ..lifecycle_manager import LifecycleManager
    from ..resource_registry import ResourceRegistry

__all__ = [
    "ResourceFactory",
]


class ResourceFactory:
    """
    Factory for creating and managing resource instances.

    This factory handles:
    - Resource creation and deduplication
    - Context-aware instantiation (root vs dependency)
    - Remote resource handling
    - Integration with LifecycleManager for state tracking
    - Proper error handling and logging

    The factory encapsulates all the logic that was previously in ResourceMeta.__call__()
    and now integrates with the centralized LifecycleManager for state management.

    Updated Architecture:
        - ResourceRegistry: Instance deduplication only
        - DependencyManager: Relationship tracking
        - LifecycleManager: State and lifecycle management (NEW)
    """

    def __init__(
        self,
        registry: "ResourceRegistry",
        dependency_manager: "DependencyManager",
        lifecycle_manager: "LifecycleManager",
    ) -> None:
        """
        Initialize the resource factory.

        Args:
            registry: Resource registry for instance tracking
            dependency_manager: Dependency manager for relationship tracking
            lifecycle_manager: Lifecycle manager for state and lifecycle operations
        """
        self._registry = registry
        self._dependency_manager = dependency_manager
        self._lifecycle_manager = lifecycle_manager

    def create_resource(
        self,
        cls: "type[Resource]",
        spec: "Spec | None" = None,
        *args: Any,
        **kwargs: Any,
    ) -> "Resource":
        """
        Create or get existing resource instance.

        This is the main factory method that handles:
        - Resource deduplication via registry
        - Context-aware instance creation
        - Proper dependency registration
        - Remote resource handling
        - Integration with LifecycleManager

        Args:
            cls: Resource class to create
            spec: Resource specification (optional)
            *args: Additional constructor arguments
            **kwargs: Additional constructor keywords

        Returns:
            New or existing resource instance

        Raises:
            CreationError: If resource creation fails
            ResourceError: For other resource-related errors
        """
        try:
            # Use empty spec if none provided
            if spec is None:
                spec = Spec(factory=cls)

            # Extract creation context
            is_dependency = kwargs.pop("__is_dependency__", False)

            # Check if this is a proxy resource request
            if isinstance(spec, ProxySpec):
                return self._create_proxy_resource(spec, is_dependency=is_dependency)

            # Try get existing instance
            instance = self._registry.get_resource(spec)
            if instance is not None:
                logger.info(f"Reusing existing resource instance: '{instance.readable_name}'")

                # Update dependency tracking
                self._dependency_manager.register_resource(instance, is_dependency=is_dependency)

                return cast("Resource", instance)
            else:
                # Create new instance
                logger.debug(f"Creating new resource instance: '{cls.factory_name()}'")

                instance = self._create_new_instance(cls, spec)

                # Register with registry for deduplication
                self._registry.add_resource(instance)

                # Register with LifecycleManager for state tracking
                self._lifecycle_manager.register_resource(instance)

                # Register with dependency manager for relationship tracking
                self._dependency_manager.register_resource(instance, is_dependency=is_dependency)

                logger.info(f"Created resource instance: '{instance.readable_name}'")
                return cast("Resource", instance)

        except (CreationError, ResourceError):
            raise
        except Exception as e:
            logger.error(f"Unexpected error creating resource: {str(e)}")
            raise ResourceError(f"Failed to create resource '{cls.factory_name()}'") from e

    # === Private Implementation ===

    def _create_new_instance(
        self,
        cls: "type[Resource]",
        spec: "Spec",
        *args: Any,
        **kwargs: Any,
    ) -> "Resource":
        """
        Create a new resource instance.

        Args:
            cls: Resource class to instantiate
            spec: Resource specification
            *args: Additional constructor arguments
            **kwargs: Additional constructor keywords

        Returns:
            New resource instance

        Raises:
            CreationError: If instantiation fails
        """
        try:
            # Call the original class constructor directly
            # This bypasses the metaclass __call__ to avoid recursion
            instance = super(type(cls), cls).__call__(spec, *args, **kwargs)  # type: ignore
            return instance
        except Exception as e:
            raise CreationError(f"Failed to instantiate '{cls.factory_name()}'") from e

    def _create_proxy_resource(self, spec: ProxySpec, is_dependency: bool = False) -> "Resource":
        """
        Create a proxy resource using RemoteResourceProxy.

        Args:
            spec: Remote resource specification
            is_dependency: Whether resource is being created as dependency

        Returns:
            RemoteResourceProxy instance

        Notes:
            - Delegates to loomistd proxy resource infrastructure
            - Remote resources get registered with all runtime components
            - Proxy handles proxy lifecycle operations
        """
        # Import here to avoid circular dependencies
        from loomicore.proxy import (
            ProxyConfigurationError,
            ProxyCoordinator,
            ProxyCoordinatorSpec,
            ResourceProxy,
        )

        logger.debug(f"Creating proxy resource for spec: {spec}")

        # Validate required fields
        if spec.inner_spec is None:
            raise ProxyConfigurationError("ProxySpec.inner_spec is required")

        if spec.client_spec is None:
            raise ProxyConfigurationError("ProxySpec.client_spec is required")

        # Validate client spec has factory
        if spec.client_spec.factory is None:
            raise ProxyConfigurationError("ProxySpec.client_spec must have a factory")

        # Validate server spec if provided
        if spec.server_spec is not None and spec.server_spec.factory is None:
            raise ProxyConfigurationError("ProxySpec.server_spec must have a factory when provided")

        logger.debug(f"Creating ProxyCoordinator for spec: {spec}")

        try:
            proxy_coordinator_spec = ProxyCoordinatorSpec(
                resource_spec=spec.inner_spec,
                client=spec.client_spec,
            )
            coordinator = ProxyCoordinator(
                proxy_coordinator_spec,
                is_dependency=is_dependency,  # type: ignore[call-arg]
            )
            proxy = ResourceProxy(coordinator)
            logger.debug(f"Successfully created ProxyCoordinator: {coordinator.readable_name}")
            return proxy
        except Exception as e:
            logger.error(f"Failed to create ProxyCoordinator for spec {spec}: {e}")
            if isinstance(e, ProxyConfigurationError):
                raise
            raise ProxyConfigurationError(f"Failed to create ProxyCoordinator: {e}") from e
