"""
Service base implementation.

This module implements the core service functionality that all services inherit.
It provides a robust foundation for building services with dependency injection,
lifecycle management, and extensible architecture.

Key Features:
- Declarative dependency specification
- Lifecycle management (initialization, shutdown)
- Thread-safe operations
- Automatic dependency cleanup
- Service state tracking
- Context manager support
- Task execution control
- Supports both sync and async runtimes

Example:
    class MyService(BaseService):
        def setup(self) -> None:
            # Initialize resources
            await self.setup_resources()

        def cleanup(self) -> None:
            # Cleanup resources
            await self.cleanup_resources()
"""

from __future__ import annotations

from typing import Any, ClassVar, TypeVar, final

from .dependency import DependencyError, DependencyManager
from .exceptions import SpecError
from .logger import logger
from .meta import ServiceMeta
from .registry import RegistryError, ServiceRegistry, ServiceState
from .spec import Spec
from .types import ServiceKey

ServiceT = TypeVar("ServiceT", bound="BaseService")


class BaseService(metaclass=ServiceMeta):
    """
    Base class for all services providing core functionality.

    This class implements fundamental service capabilities including:
    - Dependency injection and tracking
    - State management
    - Service identification

    The class is designed to be extended by concrete services that implement
    their specific initialization and shutdown logic.

    Attributes:
        spec: Service specification
        name: Service name
        key: Unique service identifier
        service_state: Current lifecycle state
        is_initialized: Whether service is fully initialized

    Example:
        class DataService(BaseService):
            def setup(self) -> None:
                await self.setup_database()

            def cleanup(self) -> None:
                await self.cleanup_database()

            with DataService() as service:
                # Service automatically initialized
                await service.process_data()
                # Service automatically shutdown after context
    """

    _registry: ClassVar[ServiceRegistry]
    _dep_manager: ClassVar[DependencyManager]

    @classmethod
    def factory_name(cls) -> str:
        return f"{cls.__module__}.{cls.__name__}"

    def __init__(self, spec: Spec | None = None) -> None:
        """
        Initialize service instance.

        Args:
            spec: Service specification defining service properties

        Raises:
            SpecError: If provided spec is invalid
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

    # --- Properties --- #

    @property
    def spec(self) -> Spec:
        """Service specification defining behavior."""
        return self._spec

    @property
    def name(self) -> str:
        """Service name for identification."""
        return self.spec.name

    @property
    def readable_name(self) -> str:
        """Service readable name for identification."""
        return ((self.spec.name + ":") if self.spec.name else "") + f"{self.__class__.__name__}"

    @property
    def key(self) -> ServiceKey:
        """Unique service identifier."""
        return self.spec.key

    @property
    def service_state(self) -> ServiceState:
        """
        Current service lifecycle state.

        Returns:
            Current ServiceState or ERROR if state unavailable
        """
        try:
            return self._registry.get_service_state(self)
        except RegistryError:
            return ServiceState.ERROR

    @property
    def is_initialized(self) -> bool:
        """Check if service is fully initialized."""
        return self.service_state == ServiceState.INITIALIZED

    # --- Dependency Management --- #

    @final
    def add_dependency(
        self,
        name: str,
        spec: Spec,
    ) -> BaseService:
        """
        Add service dependency.

        Args:
            name: Dependency name
            service: Dependency service instance

        Raises:
            DependencyError: If dependency invalid or creates cycle
        """
        try:
            return self._dep_manager.resolve_dependency(self, name, spec)
        except DependencyError as e:
            logger.error(f"Failed to add dependency '{name}' to '{self.readable_name}': {str(e)}")
            raise

    @final
    def get_dependency(self, name: str) -> BaseService:
        """
        Get named dependency if it exists.

        Args:
            name: Dependency name to retrieve

        Returns:
            Dependency service
        """
        deps = self._dep_manager.get_dependencies(self)
        if name not in deps.keys():
            raise DependencyError(
                f"Dependency '{name}' not found for service '{self.readable_name}'"
            )

        return deps[name]

    @final
    def get_dependencies(self) -> dict[str, BaseService]:
        """
        Get all service dependencies.

        Returns:
            Dict mapping dependency names to services
        """
        return self._dep_manager.get_dependencies(self)

    @final
    def get_dependents(self) -> set[BaseService]:
        """
        Get all dependent services.

        Returns:
            Set of services depending on this one
        """
        return self._dep_manager.get_dependents(self)

    @final
    def detach_dependent(self, dependent: BaseService) -> None:
        """
        Remove a dependent service.

        Args:
            dependent: Dependent service to remove
        """
        self._dep_manager.detach_relationship(dependent, self)

    # --- Methods --- #

    def __hash__(self) -> int:
        """Hash based on service key."""
        return hash(self.key)

    def __eq__(self, other: Any) -> bool:
        """Equality based on service key."""
        return isinstance(other, BaseService) and self.key == other.key

    def __repr__(self) -> str:
        """String representation including spec."""
        return f"<Service '{self.readable_name}' ('{self.service_state}'): spec=({self.spec})>"
