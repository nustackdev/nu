"""
Single resource attachment pattern.

This module provides the ResourceDescriptor for single resource attachment
via the Attach() function. It implements the most basic attach pattern where
one descriptor resolves to exactly one resource instance.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from loomicore.common.descriptor import StorageStrategy, ValidationStrategy

from ..base_descriptor import BaseResourceDescriptor
from ..exceptions import AttachError

if TYPE_CHECKING:
    from loomicore.resource import Resource
    from loomicore.runtime.dependency_manager import DependencyManager
    from loomicore.spec import Spec

__all__ = [
    "ResourceDescriptor",
    "Attach",
]


class ResourceDescriptor(BaseResourceDescriptor):
    """
    Descriptor for single resource attachment via Attach().

    This descriptor represents the simplest attach pattern where one
    descriptor attribute resolves to exactly one resource instance.
    It uses priority-based spec resolution and integrates with the
    dependency manager for resource creation and relationship tracking.

    Priority for spec resolution:
    1. Spec from parent resource's spec (if attribute exists)
    2. Spec from descriptor itself (provided to Attach())
    3. Error if no spec found

    Examples:
        ```python
        class MyService(SyncResource):
            # Spec from descriptor
            database = Attach(DatabaseSpec())

            # Spec from parent resource spec (MyServiceSpec.cache)
            cache = Attach()
        ```
    """

    def __init__(self, spec: "Spec | None" = None, /, *, alias: str | None = None) -> None:
        """
        Initialize resource descriptor.

        Args:
            spec: Resource specification for the dependency
            alias: Optional alias name for the dependency
        """
        super().__init__(
            storage=StorageStrategy.WEAKREF,
            validation_strategy=ValidationStrategy.STRICT,
            allow_none=True,
        )
        self.spec = spec
        self.alias = alias

    def _validate_type(self, value: Any) -> bool:
        """Validate that value is a resource (or None)."""
        # Allow any value since we don't have specific type constraints
        # Type safety is handled by the generic type parameter
        return True

    def _get_default(self) -> None:
        """Default value is None until resolved."""
        return None

    def resolve(
        self, parent: "Resource", name: str, dependency_manager: "DependencyManager"
    ) -> "Resource":
        """
        Resolve single resource using priority-based spec resolution.

        This method implements the core resolution logic for single resource
        attachment. It uses a priority system to determine the spec, then
        delegates to the dependency manager for actual resource creation.

        Args:
            parent: Resource containing this descriptor
            name: Attribute name of this descriptor
            dependency_manager: Dependency manager for resource operations

        Returns:
            Resolved resource instance

        Raises:
            AttachError: If spec resolution or resource creation fails
        """
        # Get spec using priority system
        spec = self._get_spec(parent, name)

        # Validate spec has factory
        if spec.factory is None:
            raise AttachError(
                f"Spec for descriptor '{name}' in '{parent.readable_name}' "
                "has no factory. Ensure spec.factory is set to a resource class."
            )

        # Delegate to dependency manager for resource creation
        try:
            return dependency_manager.resolve_dependency(parent, name, spec)
        except Exception as e:
            raise AttachError(
                f"Failed to resolve resource '{name}' with factory '{spec.factory.__name__}' "
                f"for '{parent.readable_name}': {str(e)}"
            ) from e

    def _get_spec(self, parent: "Resource", name: str) -> "Spec":
        """
        Get spec using priority: parent spec > descriptor spec.

        Args:
            parent: Parent resource
            name: Descriptor attribute name

        Returns:
            Resolved spec

        Raises:
            AttachError: If no spec found
        """
        # Priority 1: Spec from parent resource's spec
        if hasattr(parent.spec, name):
            return getattr(parent.spec, name)

        # Priority 2: Spec from descriptor
        if self.spec is not None:
            return self.spec

        # No spec found - error
        raise AttachError(
            f"No spec found for descriptor '{name}' in '{parent.readable_name}'. "
            "Either add the spec to the parent resource spec or use Attach(spec) "
            "to provide a specification."
        )


def Attach(spec: "Spec | None" = None, /, *, alias: str | None = None) -> "Resource":
    """
    Create a single resource attachment descriptor.

    This function creates a descriptor that will resolve to exactly one
    resource instance. The resource specification can be provided directly
    or inherited from the parent resource's spec.

    Args:
        spec: Optional resource specification. If not provided, the spec
              will be resolved from the parent resource's spec using the
              descriptor's attribute name.

    Returns:
        ResourceDescriptor that will resolve to a resource instance

    Examples:
        ```python
        class MyService(SyncResource):
            # Spec provided directly
            database = Attach(DatabaseSpec(url="postgresql://..."))

            # Spec from parent resource spec (MyServiceSpec.cache)
            cache = Attach()

        # Usage
        service = MyService(MyServiceSpec(
            cache=CacheSpec(size=1000)  # Spec for cache dependency
        ))

        # Access resolved resource
        result = service.database.query("SELECT * FROM users")
        service.cache.set("key", result)
        ```

    Notes:
        - Type annotation ResourceType is for static type checking
        - Actual runtime type is ResourceDescriptor
        - Resolution happens during resource composition
        - Supports priority-based spec resolution
    """
    return cast("Resource", ResourceDescriptor(spec, alias=alias))
