"""
Composition Engine - Handles resource composition with attach descriptors.

This module provides the CompositionEngine which handles discovery and resolution
of attach descriptors, resource assembly, and composition logic. It serves as the
bridge between resource classes with their declarative dependencies and the runtime
system that resolves those dependencies.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .descriptor import BaseResourceDescriptor
from .exceptions import DependencyError
from .logger import logger

if TYPE_CHECKING:
    from loomicore.patterns.attach.descriptor import ResourceDescriptor
    from loomicore.resource import Resource

    from ..dependency_manager import DependencyManager

__all__ = [
    "CompositionEngine",
]


class CompositionEngine:
    """
    Engine for composing resources with their attach descriptors.

    This engine handles:
    - Discovery of attach descriptors on resource classes
    - Resolution of descriptor values through dependency manager
    - Assembly of complete resource instances with dependencies
    - Coordination with dependency manager for relationship tracking

    The engine encapsulates all composition logic that ties together
    resources with their declared dependencies and patterns. It scans
    resource classes for descriptors and resolves them to actual resource
    instances, setting up the complete dependency graph.

    Key Features:
        - Automatic descriptor discovery via class introspection
        - Support for different descriptor types (Attach, AttachMany, etc.)
        - Integration with dependency manager for relationships
        - Comprehensive logging for debugging
    """

    def __init__(self, dependency_manager: "DependencyManager") -> None:
        """
        Initialize the composition engine.

        Args:
            dependency_manager: Dependency manager for relationship handling
        """
        self._dependency_manager = dependency_manager
        logger.debug("Initialized composition engine")

    def compose_resource(self, resource_instance: "Resource") -> None:
        """
        Compose all attach descriptors for a resource instance.

        This method discovers and resolves all attach descriptors on the resource,
        setting up the complete dependency graph. It serves as the main entry point
        for resource composition during the initialization process.

        Process:
        1. Discover all descriptors on the resource class
        2. Resolve each descriptor to an actual resource instance
        3. Set the resolved value on the resource instance
        4. Handle any composition errors with proper context

        Args:
            resource_instance: Resource to compose

        Raises:
            DependencyError: If composition fails for any descriptor

        Notes:
            - Called during resource initialization
            - Handles both simple and complex descriptor types
            - Sets up bidirectional dependency relationships
            - Comprehensive error handling and logging
        """
        logger.debug(f"Composing resource: '{resource_instance.readable_name}'")

        try:
            # Discover all descriptors on the resource
            descriptors = self.discover_descriptors(resource_instance)

            if not descriptors:
                logger.debug(f"No descriptors found for '{resource_instance.readable_name}'")
                return

            logger.debug(
                f"Found {len(descriptors)} descriptors for '{resource_instance.readable_name}': "
                f"{[name for name, _ in descriptors]}"
            )

            # Resolve each descriptor
            for name, descriptor in descriptors:
                try:
                    logger.debug(
                        f"Resolving descriptor '{name}' for '{resource_instance.readable_name}'"
                    )

                    resolved_value = self.resolve_descriptor(resource_instance, name, descriptor)

                    # Set the resolved value on the resource instance
                    setattr(resource_instance, name, resolved_value)

                    logger.debug(
                        f"Successfully resolved descriptor '{name}' for '{resource_instance.readable_name}'"
                    )

                except Exception as e:
                    error_msg = f"Failed to resolve descriptor '{name}' for '{resource_instance.readable_name}': {str(e)}"
                    logger.error(error_msg)
                    raise DependencyError(error_msg) from e

            logger.info(
                f"Successfully composed resource '{resource_instance.readable_name}' "
                f"with {len(descriptors)} dependencies"
            )

        except Exception as e:
            if isinstance(e, DependencyError):
                raise
            error_msg = f"Failed to compose resource '{resource_instance.readable_name}': {str(e)}"
            logger.error(error_msg)
            raise DependencyError(error_msg) from e

    def discover_descriptors(self, resource_instance: "Resource") -> list[tuple[str, Any]]:
        """
        Discover all attach descriptors on a resource instance.

        This method scans the resource's class hierarchy to find all descriptor
        instances that represent dependencies. It looks for instances of
        BaseDescriptor in the class attributes.

        Args:
            resource_instance: Resource to inspect

        Returns:
            List of (name, descriptor) tuples

        Notes:
            - Scans entire class hierarchy (MRO) to find inherited descriptors
            - Only returns actual descriptor instances, not other attributes
            - Preserves order of discovery for consistent behavior
            - Handles multiple inheritance properly via MRO
        """
        descriptors: list[tuple[str, Any]] = []

        # Scan the method resolution order to find all descriptors
        # This ensures we find descriptors from parent classes too
        for cls in type(resource_instance).__mro__:
            # Only scan the class's own dictionary, not inherited attributes
            # We iterate through MRO to handle inheritance properly
            for name, value in cls.__dict__.items():
                # Check if this is a descriptor we haven't seen yet
                if isinstance(value, BaseResourceDescriptor):
                    # Check if we've already found this descriptor name
                    # (could happen if overridden in subclass)
                    if not any(desc_name == name for desc_name, _ in descriptors):
                        descriptors.append((name, value))
                        logger.debug(
                            f"Discovered descriptor '{name}' of type {type(value).__name__} in class {cls.__name__}"
                        )

        logger.debug(
            f"Discovered {len(descriptors)} total descriptors for '{resource_instance.readable_name}'"
        )
        return descriptors

    def resolve_descriptor(
        self,
        resource_instance: "Resource",
        descriptor_name: str,
        descriptor: BaseResourceDescriptor,
    ) -> Resource:
        """
        Resolve a single attach descriptor to its value.

        This method takes a descriptor instance and resolves it to the actual
        resource or value it represents. It handles different descriptor types
        and coordinates with the dependency manager for relationship tracking.

        Args:
            resource_instance: Parent resource containing the descriptor
            descriptor_name: Name of the descriptor attribute
            descriptor: The descriptor instance to resolve

        Returns:
            Resolved value for the descriptor

        Raises:
            DependencyError: If descriptor resolution fails

        Notes:
            - Handles different descriptor types (Attach, AttachMany, etc.)
            - Validates descriptor configuration before resolution
            - Uses dependency manager for actual resource creation
            - Supports future extension for new descriptor types
        """
        from loomicore.patterns.attach.descriptor import ResourceDescriptor

        logger.debug(
            f"Resolving descriptor '{descriptor_name}' of type {type(descriptor).__name__} for '{resource_instance.readable_name}'"
        )

        if not isinstance(descriptor, BaseResourceDescriptor):
            raise DependencyError(
                f"Descriptor '{descriptor_name}' in '{resource_instance.readable_name}' "
                f"is not a valid descriptor type: {type(descriptor).__name__}"
            )

        # Handle ResourceDescriptor (from Attach() calls)
        if isinstance(descriptor, ResourceDescriptor):
            return self._resolve_resource_descriptor(resource_instance, descriptor_name, descriptor)

        # Handle future descriptor types here
        # elif isinstance(descriptor, AttachManyDescriptor):
        #     return self._resolve_attach_many_descriptor(...)
        # elif isinstance(descriptor, AttachPoolDescriptor):
        #     return self._resolve_attach_pool_descriptor(...)

        # Unknown descriptor type
        raise DependencyError(
            f"Unknown descriptor type '{type(descriptor).__name__}' for '{descriptor_name}' "
            f"in '{resource_instance.readable_name}'"
        )

    def _resolve_resource_descriptor(
        self,
        resource_instance: "Resource",
        descriptor_name: str,
        descriptor: "ResourceDescriptor",
    ) -> "Resource":
        """
        Resolve a ResourceDescriptor (created by Attach() calls).

        Uses priority-based spec resolution:
        1. Spec from parent resource's spec (if attribute exists)
        2. Spec from descriptor itself
        3. Error if no spec found

        Args:
            resource_instance: Parent resource
            descriptor_name: Name of the descriptor attribute
            descriptor: The ResourceDescriptor to resolve

        Returns:
            Resolved resource instance

        Raises:
            DependencyError: If resolution fails or spec is missing
        """
        # Get resource spec by priority
        spec = None

        # 1. First priority: Spec from parent resource's spec
        if hasattr(resource_instance.spec, descriptor_name):
            spec = getattr(resource_instance.spec, descriptor_name)
            logger.debug(
                f"Using spec from parent resource spec for '{descriptor_name}' "
                f"in '{resource_instance.readable_name}'"
            )

        # 2. Second priority: Spec from descriptor
        elif descriptor.spec is not None:
            spec = descriptor.spec
            logger.debug(
                f"Using spec from descriptor for '{descriptor_name}' "
                f"in '{resource_instance.readable_name}'"
            )

        # 3. No spec found - raise error
        else:
            raise DependencyError(
                f"No spec found for descriptor '{descriptor_name}' in '{resource_instance.readable_name}'. "
                "Either add the spec to the parent resource spec or use Attach(spec) to provide a specification."
            )

        # Validate spec has a factory
        if spec.factory is None:
            raise DependencyError(
                f"Spec for descriptor '{descriptor_name}' in '{resource_instance.readable_name}' "
                "has no factory. Ensure spec.factory is set to a resource class."
            )

        logger.debug(
            f"Resolving ResourceDescriptor '{descriptor_name}' with factory '{spec.factory.__name__}' "
            f"for '{resource_instance.readable_name}'"
        )

        try:
            # Use dependency manager to resolve the dependency
            # This handles resource creation, deduplication, and relationship tracking
            resolved_resource = self._dependency_manager.resolve_dependency(
                resource_instance, descriptor_name, spec
            )

            logger.debug(
                f"Successfully resolved ResourceDescriptor '{descriptor_name}' "
                f"to '{resolved_resource.readable_name}' for '{resource_instance.readable_name}'"
            )

            return resolved_resource

        except Exception as e:
            error_msg = (
                f"Failed to resolve ResourceDescriptor '{descriptor_name}' "
                f"with factory '{spec.factory.__name__}' for '{resource_instance.readable_name}': {str(e)}"
            )
            logger.error(error_msg)
            raise DependencyError(error_msg) from e

    def __repr__(self) -> str:
        """
        String representation of the composition engine for debugging.

        Returns:
            String representation showing dependency manager reference
        """
        return f"<CompositionEngine: dependency_manager={self._dependency_manager}>"
