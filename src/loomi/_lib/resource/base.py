"""
Base resource functionality shared between async and sync resources.

This module provides the common foundation for all resource types through
the ResourceCommonBase class. It implements core resource features including:
- Resource specification management
- Identity and equality handling
- Name and key generation
- Registry and dependency manager integration

The functionality here is inherited by both async and sync resource base classes
to ensure consistent behavior across all resource types.
"""

from __future__ import annotations

from abc import ABC
from types import TracebackType
from typing import TYPE_CHECKING, Any, ClassVar, Self

from .exceptions import SpecError
from .logger import logger
from .spec import Spec

if TYPE_CHECKING:
    from ..dependency_manager import DependencyManager
    from ..registry import ResourceRegistry
    from ..types import ResourceState
    from .resource import Resource


__all__ = [
    "ResourceABC",
    "AsyncResourceABC",
    "SyncResourceABC",
]


class ResourceABC(ABC):
    """
    Base class providing common functionality for all resource types.

    This class implements the core features needed by all resources, whether
    async or sync. It handles resource specifications, identity management,
    registry integration, and basic resource properties.

    Class Attributes:
        _registry (ResourceRegistry): Shared resource registry for instance tracking
        _dep_manager (DependencyManager): Shared dependency manager for resource relationships

    Attributes:
        _spec (Spec): Resource specification defining the instance's properties

    Properties:
        spec (Spec): Access to the resource specification
        name (str): Resource instance name
        readable_name (str): Human-readable resource identifier
        key (ResourceKey): Unique resource instance identifier
    """

    _registry: ClassVar["ResourceRegistry"]
    _dep_manager: ClassVar["DependencyManager"]

    @classmethod
    def factory_name(cls) -> str:
        """
        Get the fully qualified name of the resource class.

        Returns:
            str: String in format "module.ClassName"
        """
        return f"{cls.__module__}.{cls.__name__}"

    def __init__(self, spec: Spec | None = None) -> None:
        """
        Initialize a new resource instance.

        Args:
            spec: Resource specification defining instance properties. If None,
                 a default spec will be created using the class as factory.

        Raises:
            SpecError: If spec is invalid (wrong type or wrong factory)

        Notes:
            - Validates spec type and factory if provided
            - Creates default spec if none provided
            - Logs initialization details at appropriate levels
        """
        if spec is not None and not isinstance(spec, Spec):
            logger.error(f"Expected type matching SpecProtocol, got '{type(spec)}'")
            raise SpecError(f"Expected type matching SpecProtocol, got '{type(spec)}'")

        if spec is not None and spec.factory is not self.__class__:
            logger.error(f"Expected spec factory '{self.factory_name()}', got {spec.factory}")
            raise SpecError(f"Expected spec factory '{self.factory_name()}', got {spec.factory}")

        if spec is None:
            spec = Spec(factory=self.__class__, name="")
            logger.warning(f"Initializing '{self.factory_name()}' with base spec: {spec}")

        self._spec = spec
        logger.debug(f"Initialized resource '{self.readable_name}' with spec {spec}")

    @property
    def spec(self) -> Spec:
        """
        Get the resource's specification.

        Returns:
            Spec: The specification defining this resource instance
        """
        return self._spec

    @property
    def name(self) -> str:
        """
        Get the resource instance name.

        Returns:
            str: Name defined in the resource specification
        """
        return self.spec.name

    @property
    def readable_name(self) -> str:
        """
        Get a human-readable identifier for the resource.

        Returns:
            str: String combining name (if present) and class name
        """
        return ((self.spec.name + ":") if self.spec.name else "") + f"{self.__class__.__name__}"

    @property
    def key(self) -> str:
        """
        Get the unique resource instance identifier.

        Returns:
            ResourceKey: Unique key generated from the specification
        """
        return self.spec.key

    def __hash__(self) -> int:
        """
        Generate hash based on resource key.

        Returns:
            int: Hash value for the resource instance
        """
        return hash(self.key)

    def __eq__(self, other: Any) -> bool:
        """
        Compare resource instances based on their keys.

        Args:
            other: Object to compare with

        Returns:
            bool: True if other is same resource type with matching key
        """
        if other is None:
            return False
        return isinstance(other, type(self)) and self.key == other.key

    def __repr__(self) -> str:
        """
        Generate string representation of the resource.

        Returns:
            str: Human-readable string showing resource name and spec
        """
        return f"<Resource '{self.readable_name}': spec=({self.spec})>"

    """
    Resource lifecycle management methods.

    These methods are used to manage the lifecycle of the resource,
    including initialization and shutdown.
    They are not intended to be used directly by resource users.
    """

    @property
    def _is_initialized(self) -> bool:
        """Check if resource is fully initialized."""
        ...

    @property
    def _resource_state(self) -> ResourceState:
        """
        Get the current lifecycle state of the resource.

        Returns:
            str: Current state of the resource
        """
        ...

    """
    Dependency management methods.
    These methods are used to manage resource dependencies and relationships.
    They are not intended to be used directly by resource users.
    """

    def _add_dependency(
        self,
        name: str,
        spec: "Spec",
    ) -> "Resource":
        """
        Add resource dependency.

        Args:
            name: Dependency name
            resource: Dependency resource instance

        Raises:
            DependencyError: If dependency invalid or creates cycle
        """
        ...

    def _get_dependency(self, name: str) -> "Resource":
        """
        Get named dependency if it exists.

        Args:
            name: Dependency name to retrieve

        Returns:
            Dependency resource
        """
        ...

    def _get_dependencies(self) -> dict[str, "Resource"]:
        """
        Get all resource dependencies.

        Returns:
            Dict mapping dependency names to resources
        """
        ...

    def _get_dependents(self) -> set["Resource"]:
        """
        Get all dependent resources.

        Returns:
            Set of resources depending on this one
        """
        ...

    def _detach_dependent(self, dependent: "Resource") -> None:
        """
        Remove a dependent resource.

        Args:
            dependent: Dependent resource to remove
        """
        ...

    def _initialize_attach_descriptors(self) -> None:
        """
        Initialize resource dependency descriptors.
        """
        ...


class SyncResourceABC(ResourceABC):
    """
    Synchronous resource initializer protocol.

    This protocol defines the interface for resources initialization.
    """

    def initialize(self) -> None:
        """
        Initialize resource and its dependencies synchronously.
        """
        ...

    def shutdown(self) -> None:
        """
        Shutdown resource and cleanup dependencies synchronously.
        """
        ...

    def __enter__(self) -> Self:
        """
        Enter context, initializing resource.

        Returns:
            Self for context usage
        """
        ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Exit context, shutting down resource."""
        ...

    def setup(self) -> None:
        """
        Resource-specific setup.

        This method should be implemented by concrete resources to
        perform their specific setup requirements
        (opening connections, configuring resource, etc).
        """
        ...

    def cleanup(self) -> None:
        """
        Resource-specific cleanup.

        This method should be implemented by concrete resources to
        perform their specific cleanup requirements.
        """
        ...

    def pre_initialize(self) -> None:
        """
        Pre-initialization hook.

        This method is called before resource initialization.

        Raises:
            InitializationError: If pre-initialization fails
        """
        ...

    def post_initialize(self) -> None:
        """
        Post-initialization hook.

        This method is called after resource initialization.

        Raises:
            InitializationError: If post-initialization fails
        """
        ...

    def pre_shutdown(self) -> None:
        """
        Pre-shutdown hook.

        This method is called before resource shutdown.

        Raises:
            ShutdownError: If pre-shutdown fails
        """
        ...

    def post_shutdown(self) -> None:
        """
        Post-shutdown hook.

        This method is called after resource shutdown.

        Raises:
            ShutdownError: If post-shutdown fails
        """
        ...


class AsyncResourceABC(ResourceABC):
    """
    Async resource initializer protocol.

    This protocol defines the interface for resources initialization.
    """

    async def initialize(self) -> None:
        """
        Initialize resource and its dependencies asynchronously.
        """
        ...

    async def shutdown(self) -> None:
        """
        Shutdown resource and cleanup dependencies asynchronously.
        """
        ...

    async def __aenter__(self) -> Self:
        """
        Enter async context, initializing resource.

        Returns:
            Self for context usage
        """
        ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Exit async context, shutting down resource."""
        ...

    async def setup(self) -> None:
        """
        Resource-specific setup.

        This method should be implemented by concrete resources to
        perform their specific setup requirements
        (opening connections, configuring resource, etc).
        """
        ...

    async def cleanup(self) -> None:
        """
        Resource-specific cleanup.

        This method should be implemented by concrete resources to
        perform their specific cleanup requirements.
        """
        ...

    async def pre_initialize(self) -> None:
        """
        Pre-initialization hook.

        This method is called before resource initialization.

        Raises:
            InitializationError: If pre-initialization fails
        """
        ...

    async def post_initialize(self) -> None:
        """
        Post-initialization hook.

        This method is called after resource initialization.

        Raises:
            InitializationError: If post-initialization fails
        """
        ...

    async def pre_shutdown(self) -> None:
        """
        Pre-shutdown hook.

        This method is called before resource shutdown.

        Raises:
            ShutdownError: If pre-shutdown fails
        """
        ...

    async def post_shutdown(self) -> None:
        """
        Post-shutdown hook.

        This method is called after resource shutdown.

        Raises:
            ShutdownError: If post-shutdown fails
        """
        ...
