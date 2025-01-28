from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING, Any, ClassVar, Self, final

if TYPE_CHECKING:
    from .base import ServiceKey, ServiceState, ServiceType, Spec
    from .lib.dependency_manager import DependencyManager
    from .lib.service_registry import ServiceRegistry


class ServiceCommonBaseProtocol(ABC):
    _registry: ClassVar["ServiceRegistry"]
    _dep_manager: ClassVar["DependencyManager"]

    @classmethod
    def factory_name(cls) -> str:
        raise NotImplementedError

    @property
    def spec(self) -> "Spec":
        raise NotImplementedError

    @property
    def name(self) -> str:
        raise NotImplementedError

    @property
    def readable_name(self) -> str:
        raise NotImplementedError

    @property
    def key(self) -> ServiceKey:
        raise NotImplementedError

    @property
    def service_state(self) -> "ServiceState":
        raise NotImplementedError

    @property
    def is_initialized(self) -> bool:
        raise NotImplementedError

    def __hash__(self) -> int:
        """Hash based on service key."""
        raise NotImplementedError

    def __eq__(self, other: Any) -> bool:
        """Equality based on service key."""
        raise NotImplementedError

    def __repr__(self) -> str:
        """String representation including spec."""
        raise NotImplementedError


class ServiceInitializerSyncProtocol(ABC):
    """
    Synchronous service initializer protocol.

    This protocol defines the interface for services initialization.
    """

    def initialize(self) -> None:
        """
        Initialize service and its dependencies synchronously.
        """
        raise NotImplementedError

    def shutdown(self) -> None:
        """
        Shutdown service and cleanup dependencies synchronously.
        """

    def __enter__(self) -> Self:
        """
        Enter context, initializing service.

        Returns:
            Self for context usage
        """
        raise NotImplementedError

    def __exit__(self, *exc_info: Any) -> None:
        """Exit context, shutting down service."""

    def setup(self) -> None:
        """
        Service-specific setup.

        This method should be implemented by concrete services to
        perform their specific setup requirements
        (opening connections, configuring service, etc).
        """
        raise NotImplementedError

    def cleanup(self) -> None:
        """
        Service-specific cleanup.

        This method should be implemented by concrete services to
        perform their specific cleanup requirements.
        """
        raise NotImplementedError

    def pre_initialize(self) -> None:
        """
        Pre-initialization hook.

        This method is called before service initialization.

        Raises:
            InitializationError: If pre-initialization fails
        """
        raise NotImplementedError

    def post_initialize(self) -> None:
        """
        Post-initialization hook.

        This method is called after service initialization.

        Raises:
            InitializationError: If post-initialization fails
        """
        raise NotImplementedError

    def pre_shutdown(self) -> None:
        """
        Pre-shutdown hook.

        This method is called before service shutdown.

        Raises:
            ShutdownError: If pre-shutdown fails
        """
        raise NotImplementedError

    def post_shutdown(self) -> None:
        """
        Post-shutdown hook.

        This method is called after service shutdown.

        Raises:
            ShutdownError: If post-shutdown fails
        """
        raise NotImplementedError


class ServiceInitializerAsyncProtocol(ABC):
    """
    Async service initializer protocol.

    This protocol defines the interface for services initialization.
    """

    async def initialize(self) -> None:
        """
        Initialize service and its dependencies asynchronously.
        """
        raise NotImplementedError

    async def shutdown(self) -> None:
        """
        Shutdown service and cleanup dependencies asynchronously.
        """

    async def __aenter__(self) -> Self:
        """
        Enter async context, initializing service.

        Returns:
            Self for context usage
        """
        raise NotImplementedError

    async def __aexit__(self, *exc_info: Any) -> None:
        """Exit async context, shutting down service."""

    async def setup(self) -> None:
        """
        Service-specific setup.

        This method should be implemented by concrete services to
        perform their specific setup requirements
        (opening connections, configuring service, etc).
        """
        raise NotImplementedError

    async def cleanup(self) -> None:
        """
        Service-specific cleanup.

        This method should be implemented by concrete services to
        perform their specific cleanup requirements.
        """
        raise NotImplementedError

    async def pre_initialize(self) -> None:
        """
        Pre-initialization hook.

        This method is called before service initialization.

        Raises:
            InitializationError: If pre-initialization fails
        """
        raise NotImplementedError

    async def post_initialize(self) -> None:
        """
        Post-initialization hook.

        This method is called after service initialization.

        Raises:
            InitializationError: If post-initialization fails
        """
        raise NotImplementedError

    async def pre_shutdown(self) -> None:
        """
        Pre-shutdown hook.

        This method is called before service shutdown.

        Raises:
            ShutdownError: If pre-shutdown fails
        """
        raise NotImplementedError

    async def post_shutdown(self) -> None:
        """
        Post-shutdown hook.

        This method is called after service shutdown.

        Raises:
            ShutdownError: If post-shutdown fails
        """
        raise NotImplementedError


class ServiceComposerProtocol(ABC):
    """
    Async service composer protocol.

    This protocol defines the interface for services composition.

    ATM, no methods are defined, this is a placeholder for future use.
    """

    @final
    def add_dependency(
        self,
        name: str,
        spec: Spec,
    ) -> "ServiceType":
        """
        Add service dependency.

        Args:
            name: Dependency name
            service: Dependency service instance

        Raises:
            DependencyError: If dependency invalid or creates cycle
        """
        raise NotImplementedError

    @final
    def get_dependency(self, name: str) -> "ServiceType":
        """
        Get named dependency if it exists.

        Args:
            name: Dependency name to retrieve

        Returns:
            Dependency service
        """
        raise NotImplementedError

    @final
    def get_dependencies(self) -> dict[str, "ServiceType"]:
        """
        Get all service dependencies.

        Returns:
            Dict mapping dependency names to services
        """
        raise NotImplementedError

    @final
    def get_dependents(self) -> set["ServiceType"]:
        """
        Get all dependent services.

        Returns:
            Set of services depending on this one
        """
        raise NotImplementedError

    @final
    def detach_dependent(self, dependent: "ServiceType") -> None:
        """
        Remove a dependent service.

        Args:
            dependent: Dependent service to remove
        """
        raise NotImplementedError


class ServiceCommonProtocol(
    ServiceCommonBaseProtocol,
    ServiceComposerProtocol,
):
    pass


class ServiceAsyncProtocol(
    ServiceCommonProtocol,
    ServiceInitializerAsyncProtocol,
):
    """
    Service protocol.

    This protocol defines the interface for services.

    ATM, no methods are defined, this is a placeholder for future use.
    """

    pass


class ServiceSyncProtocol(
    ServiceCommonProtocol,
    ServiceInitializerSyncProtocol,
):
    """
    Sync service protocol.

    This protocol defines the interface for services.

    ATM, no methods are defined, this is a placeholder for future use.
    """

    pass
