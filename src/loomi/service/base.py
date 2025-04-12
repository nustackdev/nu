"""
Base service functionality shared between async and sync services.

This module provides the common foundation for all service types through
the ServiceCommonBase class. It implements core service features including:
- Service specification management
- Identity and equality handling
- Name and key generation
- Registry and dependency manager integration

The functionality here is inherited by both async and sync service base classes
to ensure consistent behavior across all service types.
"""

from __future__ import annotations

from abc import ABC
from types import TracebackType
from typing import TYPE_CHECKING, Any, ClassVar, Self

from loomi.spec import Spec

from .exceptions import SpecError
from .logger import logger

if TYPE_CHECKING:
    from loomi.lib.dependency_manager import DependencyManager
    from loomi.lib.service_registry import ServiceRegistry

    from .service import Service
    from .types import ServiceState


__all__ = [
    "ServiceABC",
    "AsyncServiceABC",
    "SyncServiceABC",
]


class ServiceABC(ABC):
    """
    Base class providing common functionality for all service types.

    This class implements the core features needed by all services, whether
    async or sync. It handles service specifications, identity management,
    registry integration, and basic service properties.

    Class Attributes:
        _registry (ServiceRegistry): Shared service registry for instance tracking
        _dep_manager (DependencyManager): Shared dependency manager for service relationships

    Attributes:
        _spec (Spec): Service specification defining the instance's properties

    Properties:
        spec (Spec): Access to the service specification
        name (str): Service instance name
        readable_name (str): Human-readable service identifier
        key (ServiceKey): Unique service instance identifier
    """

    _registry: ClassVar["ServiceRegistry"]
    _dep_manager: ClassVar["DependencyManager"]

    @classmethod
    def factory_name(cls) -> str:
        """
        Get the fully qualified name of the service class.

        Returns:
            str: String in format "module.ClassName"
        """
        return f"{cls.__module__}.{cls.__name__}"

    def __init__(self, spec: Spec | None = None) -> None:
        """
        Initialize a new service instance.

        Args:
            spec: Service specification defining instance properties. If None,
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
        logger.debug(f"Initialized service '{self.readable_name}' with spec {spec}")

    @property
    def spec(self) -> Spec:
        """
        Get the service's specification.

        Returns:
            Spec: The specification defining this service instance
        """
        return self._spec

    @property
    def name(self) -> str:
        """
        Get the service instance name.

        Returns:
            str: Name defined in the service specification
        """
        return self.spec.name

    @property
    def readable_name(self) -> str:
        """
        Get a human-readable identifier for the service.

        Returns:
            str: String combining name (if present) and class name
        """
        return ((self.spec.name + ":") if self.spec.name else "") + f"{self.__class__.__name__}"

    @property
    def key(self) -> str:
        """
        Get the unique service instance identifier.

        Returns:
            ServiceKey: Unique key generated from the specification
        """
        return self.spec.key

    def __hash__(self) -> int:
        """
        Generate hash based on service key.

        Returns:
            int: Hash value for the service instance
        """
        return hash(self.key)

    def __eq__(self, other: Any) -> bool:
        """
        Compare service instances based on their keys.

        Args:
            other: Object to compare with

        Returns:
            bool: True if other is same service type with matching key
        """
        if other is None:
            return False
        return isinstance(other, type(self)) and self.key == other.key

    def __repr__(self) -> str:
        """
        Generate string representation of the service.

        Returns:
            str: Human-readable string showing service name and spec
        """
        return f"<Service '{self.readable_name}': spec=({self.spec})>"

    """
    Service lifecycle management methods.

    These methods are used to manage the lifecycle of the service,
    including initialization and shutdown.
    They are not intended to be used directly by service users.
    """

    @property
    def _is_initialized(self) -> bool:
        """Check if service is fully initialized."""
        ...

    @property
    def _service_state(self) -> ServiceState:
        """
        Get the current lifecycle state of the service.

        Returns:
            str: Current state of the service
        """
        ...

    """
    Dependency management methods.
    These methods are used to manage service dependencies and relationships.
    They are not intended to be used directly by service users.
    """

    def _add_dependency(
        self,
        name: str,
        spec: "Spec",
    ) -> "Service":
        """
        Add service dependency.

        Args:
            name: Dependency name
            service: Dependency service instance

        Raises:
            DependencyError: If dependency invalid or creates cycle
        """
        ...

    def _get_dependency(self, name: str) -> "Service":
        """
        Get named dependency if it exists.

        Args:
            name: Dependency name to retrieve

        Returns:
            Dependency service
        """
        ...

    def _get_dependencies(self) -> dict[str, "Service"]:
        """
        Get all service dependencies.

        Returns:
            Dict mapping dependency names to services
        """
        ...

    def _get_dependents(self) -> set["Service"]:
        """
        Get all dependent services.

        Returns:
            Set of services depending on this one
        """
        ...

    def _detach_dependent(self, dependent: "Service") -> None:
        """
        Remove a dependent service.

        Args:
            dependent: Dependent service to remove
        """
        ...

    def _initialize_attach_descriptors(self) -> None:
        """
        Initialize service dependency descriptors.
        """
        ...


class SyncServiceABC(ServiceABC):
    """
    Synchronous service initializer protocol.

    This protocol defines the interface for services initialization.
    """

    def initialize(self) -> None:
        """
        Initialize service and its dependencies synchronously.
        """
        ...

    def shutdown(self) -> None:
        """
        Shutdown service and cleanup dependencies synchronously.
        """
        ...

    def __enter__(self) -> Self:
        """
        Enter context, initializing service.

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
        """Exit context, shutting down service."""
        ...

    def setup(self) -> None:
        """
        Service-specific setup.

        This method should be implemented by concrete services to
        perform their specific setup requirements
        (opening connections, configuring service, etc).
        """
        ...

    def cleanup(self) -> None:
        """
        Service-specific cleanup.

        This method should be implemented by concrete services to
        perform their specific cleanup requirements.
        """
        ...

    def pre_initialize(self) -> None:
        """
        Pre-initialization hook.

        This method is called before service initialization.

        Raises:
            InitializationError: If pre-initialization fails
        """
        ...

    def post_initialize(self) -> None:
        """
        Post-initialization hook.

        This method is called after service initialization.

        Raises:
            InitializationError: If post-initialization fails
        """
        ...

    def pre_shutdown(self) -> None:
        """
        Pre-shutdown hook.

        This method is called before service shutdown.

        Raises:
            ShutdownError: If pre-shutdown fails
        """
        ...

    def post_shutdown(self) -> None:
        """
        Post-shutdown hook.

        This method is called after service shutdown.

        Raises:
            ShutdownError: If post-shutdown fails
        """
        ...


class AsyncServiceABC(ServiceABC):
    """
    Async service initializer protocol.

    This protocol defines the interface for services initialization.
    """

    async def initialize(self) -> None:
        """
        Initialize service and its dependencies asynchronously.
        """
        ...

    async def shutdown(self) -> None:
        """
        Shutdown service and cleanup dependencies asynchronously.
        """
        ...

    async def __aenter__(self) -> Self:
        """
        Enter async context, initializing service.

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
        """Exit async context, shutting down service."""
        ...

    async def setup(self) -> None:
        """
        Service-specific setup.

        This method should be implemented by concrete services to
        perform their specific setup requirements
        (opening connections, configuring service, etc).
        """
        ...

    async def cleanup(self) -> None:
        """
        Service-specific cleanup.

        This method should be implemented by concrete services to
        perform their specific cleanup requirements.
        """
        ...

    async def pre_initialize(self) -> None:
        """
        Pre-initialization hook.

        This method is called before service initialization.

        Raises:
            InitializationError: If pre-initialization fails
        """
        ...

    async def post_initialize(self) -> None:
        """
        Post-initialization hook.

        This method is called after service initialization.

        Raises:
            InitializationError: If post-initialization fails
        """
        ...

    async def pre_shutdown(self) -> None:
        """
        Pre-shutdown hook.

        This method is called before service shutdown.

        Raises:
            ShutdownError: If pre-shutdown fails
        """
        ...

    async def post_shutdown(self) -> None:
        """
        Post-shutdown hook.

        This method is called after service shutdown.

        Raises:
            ShutdownError: If post-shutdown fails
        """
        ...
