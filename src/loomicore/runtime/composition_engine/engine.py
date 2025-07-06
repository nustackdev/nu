"""
Composition Engine - Handles resource composition with attach descriptors.

This module provides the CompositionEngine which handles discovery and resolution
of attach descriptors, resource assembly, and composition logic. It serves as the
bridge between resource classes with their declarative dependencies and the runtime
system that resolves those dependencies.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from loomicore.attach import BaseResourceDescriptor

from .exceptions import DependencyError
from .logger import logger

if TYPE_CHECKING:
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
    - Resolution of descriptor values through self-resolution
    - Assembly of complete resource instances with dependencies
    - Coordination with dependency manager for relationship tracking

    The engine encapsulates all composition logic that ties together
    resources with their declared dependencies and patterns. It scans
    resource classes for descriptors and resolves them using each
    descriptor's own resolution logic.

    Key Features:
        - Automatic descriptor discovery via class introspection
        - Self-resolving descriptors (no pattern-specific logic needed)
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
        2. Resolve each descriptor using its own resolution logic
        3. Set the resolved value on the resource instance
        4. Handle any composition errors with proper context

        Args:
            resource_instance: Resource to compose

        Raises:
            DependencyError: If composition fails for any descriptor

        Notes:
            - Called during resource initialization
            - Handles all descriptor types through self-resolution
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
        BaseResourceDescriptor in the class attributes.

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
    ) -> Any:
        """
        Resolve a single attach descriptor to its value using self-resolution.

        This method delegates to the descriptor's own resolve() method, allowing
        each descriptor type to handle its own resolution logic. This eliminates
        the need for pattern-specific conditional logic in the composition engine.

        Args:
            resource_instance: Parent resource containing the descriptor
            descriptor_name: Name of the descriptor attribute
            descriptor: The descriptor instance to resolve

        Returns:
            Resolved value for the descriptor (Resource, Coordinator, etc.)

        Raises:
            DependencyError: If descriptor resolution fails

        Notes:
            - Uses descriptor's self-resolution capability
            - No pattern-specific logic needed here
            - Supports any descriptor type that implements resolve()
            - Clean separation of concerns
        """
        logger.debug(
            f"Resolving descriptor '{descriptor_name}' of type {type(descriptor).__name__} "
            f"for '{resource_instance.readable_name}'"
        )

        if not isinstance(descriptor, BaseResourceDescriptor):
            raise DependencyError(
                f"Descriptor '{descriptor_name}' in '{resource_instance.readable_name}' "
                f"is not a valid descriptor type: {type(descriptor).__name__}"
            )

        try:
            # Delegate to descriptor's self-resolution method
            resolved_value = descriptor.resolve(
                resource_instance, descriptor_name, self._dependency_manager
            )

            logger.debug(
                f"Successfully resolved descriptor '{descriptor_name}' "
                f"to {type(resolved_value).__name__} for '{resource_instance.readable_name}'"
            )

            return resolved_value

        except Exception as e:
            error_msg = (
                f"Failed to resolve descriptor '{descriptor_name}' of type {type(descriptor).__name__} "
                f"for '{resource_instance.readable_name}': {str(e)}"
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
