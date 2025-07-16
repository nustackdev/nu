"""
BaseResource - common functionality shared by all resource types.

This module provides the BaseResource class that implements core resource
functionality without any runtime dependencies. This avoids circular imports
while providing essential resource identity and behavior.

The BaseResource class handles:
- Resource specification management
- Identity properties (key, name, readable_name)
- Equality and hashing based on resource key
- String representation for debugging

All operational logic (lifecycle, dependencies, state management) is
deliberately excluded to avoid runtime dependencies and circular imports.
That functionality is provided by concrete resource classes through delegation.
"""

from __future__ import annotations

from typing import Any, cast, final

from loomicore.runtime import get_dependency_manager, get_lifecycle_manager
from loomicore.spec import ResourceSpec, Spec
from loomicore.types import ResourceState

__all__ = [
    "BaseResource",
]


class BaseResource:
    """
    Base resource class providing core identity and behavior.

    This class provides the fundamental properties and behavior shared by all
    resource types without any dependencies on the runtime system. It handles
    resource identity, equality, and representation while leaving operational
    concerns to concrete implementations.

    The class is designed to be inherited by SyncResource and AsyncResource,
    which add lifecycle management through delegation to the runtime system.

    Attributes:
        _spec: Resource specification defining the instance's properties

    Properties:
        spec: Access to the resource specification
        key: Unique resource identifier derived from spec
        name: Human-readable resource name from spec
        readable_name: Combined name and class for display purposes

    Design Notes:
        - No runtime imports to avoid circular dependencies
        - Pure identity and behavior, no operational logic
        - Immutable identity based on specification
        - Thread-safe through immutability
    """

    @final
    def __init__(self, spec: Spec | None = None, /) -> None:
        """
        Initialize base resource with specification.

        Creates a resource instance with the given specification. If no spec
        is provided, creates a default spec using the class as factory.

        Args:
            spec: Resource specification defining instance properties.
                 If None, creates default spec with class as factory.

        Notes:
            The specification becomes the immutable identity of the resource.
            All resource behavior and properties derive from this spec.
        """
        if spec is None:
            spec = ResourceSpec(factory=self.__class__, name="")

        # spec is ensured to be a ResourceSpec, as metaclass transforms any spec to ResourceSpec
        # before passing it to the resource
        self._spec = cast(ResourceSpec, spec)

    # === Identity Properties ===

    @classmethod
    def factory_name(cls) -> str:
        """
        Get the fully qualified name of the resource class.

        Provides a unique identifier for the resource class that can be
        used by the runtime system for registration, logging, and debugging.

        Returns:
            String in format "module.ClassName" for unique identification

        Example:
            "myapp.services.DatabaseService"
        """
        return f"{cls.__module__}.{cls.__name__}"

    @property
    def spec(self) -> ResourceSpec:
        """
        Get the resource's specification.

        The specification defines all properties and behavior of the resource
        instance. It serves as the immutable identity and configuration.

        Returns:
            The specification used to create this resource instance
        """
        return self._spec

    @property
    def key(self) -> str:
        """
        Get the unique resource identifier.

        The key is derived from the resource specification and uniquely
        identifies this resource instance. Resources with identical specs
        will have identical keys, enabling deduplication.

        Returns:
            Unique string identifier for this resource instance
        """
        return self.spec.key

    @property
    def name(self) -> str:
        """
        Get the resource instance name.

        Returns the human-readable name defined in the resource specification.
        This name is typically used for logging and debugging purposes.

        Returns:
            Resource name from specification, may be empty string
        """
        return self.spec.name

    @property
    def readable_name(self) -> str:
        """
        Get a human-readable identifier for the resource.

        Combines the resource name (if present) with the class name to create
        a clear identifier for logging, debugging, and user display.

        Returns:
            String in format "name:ClassName" or just "ClassName" if no name

        Examples:
            - Resource with name "db": "db:DatabaseService"
            - Resource without name: "DatabaseService"
        """
        if self.name:
            return f"{self.name}:{self.__class__.__name__}"
        return self.__class__.__name__

    # === Equality and Hashing ===

    def __hash__(self) -> int:
        """
        Generate hash based on resource key.

        Resources are hashed by their unique key, allowing them to be used
        in sets and as dictionary keys. Resources with identical specs will
        have identical hashes.

        Returns:
            Hash value derived from resource key
        """
        return hash(self.key)

    def __eq__(self, other: Any) -> bool:
        """
        Compare resource instances based on their keys.

        Two resources are considered equal if they are the same type and
        have the same key (derived from identical specifications).

        Args:
            other: Object to compare with this resource

        Returns:
            True if other is same resource type with matching key
        """
        if other is None:
            return False
        return isinstance(other, type(self)) and self.key == other.key

    def __repr__(self) -> str:
        """
        Generate string representation of the resource.

        Creates a debug-friendly string showing the resource type and
        readable name for easy identification in logs and debugging.

        Returns:
            String representation in format "<ClassName 'readable_name'>"

        Example:
            "<DatabaseService 'db:DatabaseService'>"
        """
        return f"<{self.__class__.__name__} '{self.readable_name}'>"

    # === State Properties ===

    @property
    def is_initialized(self) -> bool:
        """
        Check if resource is fully initialized and ready for use.

        A resource is considered initialized when:
        - All dependencies have been resolved and initialized
        - The setup() method has completed successfully
        - Resource state is tracked as INITIALIZED in runtime

        Returns:
            True if resource is fully initialized and operational

        Notes:
            - Safe to call before initialization (returns False)
            - Delegates to runtime for accurate state tracking
            - Thread-safe through runtime coordination
        """
        return get_lifecycle_manager().is_resource_initialized(self)  # type: ignore[return-value]

    @property
    def resource_state(self) -> ResourceState:
        """
        Get the current lifecycle state of the resource.

        Returns the current state from the runtime system, which tracks
        the resource through its complete lifecycle from creation to shutdown.

        Possible states:
            - CREATED: Initial state after instance creation
            - INITIALIZING: Resource is starting up
            - INITIALIZED: Resource is ready for operation
            - SHUTTING_DOWN: Resource is in the process of shutting down
            - SHUTDOWN: Resource has completed shutdown
            - ERROR: Resource encountered an error

        Returns:
            Current ResourceState enum value

        Notes:
            - Delegates to runtime for accurate state tracking
            - Thread-safe through runtime coordination
            - Returns ERROR state if runtime tracking fails
            - Useful for debugging and monitoring resource lifecycle
        """
        return get_lifecycle_manager().get_resource_state(self)  # type: ignore[return-value]

    # === Dependency Introspection ===

    def get_dependencies(self) -> dict[str, "BaseResource"]:
        """
        Get all dependencies of this resource.

        Returns a mapping of dependency names to their resolved resource instances.
        These are the resources that this resource depends on, typically defined
        via Attach descriptors on the resource class.

        Returns:
            Dictionary mapping dependency names to resource instances

        Example:
            ```python
            class MyService(SyncResource):
                database = Attach(DatabaseSpec())
                cache = Attach(CacheSpec())

            service = MyService(spec)
            deps = service.get_dependencies()
            # deps = {'database': <DatabaseService>, 'cache': <CacheService>}

            # Access specific dependency
            if 'database' in deps:
                deps['database'].query("SELECT 1")
            ```

        Notes:
            - Only returns resolved dependencies (after composition)
            - Empty dict if no dependencies or before composition
            - Thread-safe through runtime delegation
            - Useful for debugging and introspection
        """
        return get_dependency_manager().get_dependencies(self)  # type: ignore[return-value]

    def get_dependents(self) -> set["BaseResource"]:
        """
        Get all resources that depend on this resource.

        Returns a set of resource instances that have this resource as
        a dependency. These are resources that would be affected if this
        resource were to be shut down.

        Returns:
            Set of resource instances that depend on this resource

        Example:
            ```python
            # If ServiceA and ServiceB both depend on DatabaseService
            db = DatabaseService(spec)
            dependents = db.get_dependents()
            # dependents = {<ServiceA>, <ServiceB>}

            # Check impact before shutdown
            if dependents:
                print(f"Shutting down database will affect {len(dependents)} services")
            ```

        Notes:
            - Empty set if no resources depend on this one
            - Updated dynamically as dependencies are created/destroyed
            - Thread-safe through runtime delegation
            - Useful for understanding impact of shutting down this resource
        """
        return get_dependency_manager().get_dependents(self)  # type: ignore[return-value]
