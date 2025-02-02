from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol, Self, final, runtime_checkable

from .exceptions import HandlerNotImplemented

if TYPE_CHECKING:
    from .base import ServiceKey, ServiceState, ServiceType, Spec


@runtime_checkable
class ServiceCommonBaseProtocol(Protocol):
    @classmethod
    def factory_name(cls) -> str:
        raise HandlerNotImplemented

    @property
    def spec(self) -> "Spec":
        raise HandlerNotImplemented

    @property
    def name(self) -> str:
        raise HandlerNotImplemented

    @property
    def readable_name(self) -> str:
        raise HandlerNotImplemented

    @property
    def key(self) -> ServiceKey:
        raise HandlerNotImplemented

    @property
    def service_state(self) -> "ServiceState":
        raise HandlerNotImplemented

    @property
    def is_initialized(self) -> bool:
        raise HandlerNotImplemented

    def __hash__(self) -> int:
        """Hash based on service key."""
        raise HandlerNotImplemented

    def __eq__(self, other: Any) -> bool:
        """Equality based on service key."""
        raise HandlerNotImplemented

    def __repr__(self) -> str:
        """String representation including spec."""
        raise HandlerNotImplemented


@runtime_checkable
class ServiceInitializerSyncProtocol(Protocol):
    """
    Synchronous service initializer protocol.

    This protocol defines the interface for services initialization.
    """

    def initialize(self) -> None:
        """
        Initialize service and its dependencies synchronously.
        """
        raise HandlerNotImplemented

    def shutdown(self) -> None:
        """
        Shutdown service and cleanup dependencies synchronously.
        """
        raise HandlerNotImplemented

    def __enter__(self) -> Self:
        """
        Enter context, initializing service.

        Returns:
            Self for context usage
        """
        raise HandlerNotImplemented

    def __exit__(self, *exc_info: Any) -> None:
        """Exit context, shutting down service."""
        raise HandlerNotImplemented

    def setup(self) -> None:
        """
        Service-specific setup.

        This method should be implemented by concrete services to
        perform their specific setup requirements
        (opening connections, configuring service, etc).
        """
        raise HandlerNotImplemented

    def cleanup(self) -> None:
        """
        Service-specific cleanup.

        This method should be implemented by concrete services to
        perform their specific cleanup requirements.
        """
        raise HandlerNotImplemented

    def pre_initialize(self) -> None:
        """
        Pre-initialization hook.

        This method is called before service initialization.

        Raises:
            InitializationError: If pre-initialization fails
        """
        raise HandlerNotImplemented

    def post_initialize(self) -> None:
        """
        Post-initialization hook.

        This method is called after service initialization.

        Raises:
            InitializationError: If post-initialization fails
        """
        raise HandlerNotImplemented

    def pre_shutdown(self) -> None:
        """
        Pre-shutdown hook.

        This method is called before service shutdown.

        Raises:
            ShutdownError: If pre-shutdown fails
        """
        raise HandlerNotImplemented

    def post_shutdown(self) -> None:
        """
        Post-shutdown hook.

        This method is called after service shutdown.

        Raises:
            ShutdownError: If post-shutdown fails
        """
        raise HandlerNotImplemented


@runtime_checkable
class ServiceInitializerAsyncProtocol(Protocol):
    """
    Async service initializer protocol.

    This protocol defines the interface for services initialization.
    """

    async def initialize(self) -> None:
        """
        Initialize service and its dependencies asynchronously.
        """
        raise HandlerNotImplemented

    async def shutdown(self) -> None:
        """
        Shutdown service and cleanup dependencies asynchronously.
        """
        raise HandlerNotImplemented

    async def __aenter__(self) -> Self:
        """
        Enter async context, initializing service.

        Returns:
            Self for context usage
        """
        raise HandlerNotImplemented

    async def __aexit__(self, *exc_info: Any) -> None:
        """Exit async context, shutting down service."""
        raise HandlerNotImplemented

    async def setup(self) -> None:
        """
        Service-specific setup.

        This method should be implemented by concrete services to
        perform their specific setup requirements
        (opening connections, configuring service, etc).
        """
        raise HandlerNotImplemented

    async def cleanup(self) -> None:
        """
        Service-specific cleanup.

        This method should be implemented by concrete services to
        perform their specific cleanup requirements.
        """
        raise HandlerNotImplemented

    async def pre_initialize(self) -> None:
        """
        Pre-initialization hook.

        This method is called before service initialization.

        Raises:
            InitializationError: If pre-initialization fails
        """
        raise HandlerNotImplemented

    async def post_initialize(self) -> None:
        """
        Post-initialization hook.

        This method is called after service initialization.

        Raises:
            InitializationError: If post-initialization fails
        """
        raise HandlerNotImplemented

    async def pre_shutdown(self) -> None:
        """
        Pre-shutdown hook.

        This method is called before service shutdown.

        Raises:
            ShutdownError: If pre-shutdown fails
        """
        raise HandlerNotImplemented

    async def post_shutdown(self) -> None:
        """
        Post-shutdown hook.

        This method is called after service shutdown.

        Raises:
            ShutdownError: If post-shutdown fails
        """
        raise HandlerNotImplemented


@runtime_checkable
class ServiceComposerProtocol(Protocol):
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
        raise HandlerNotImplemented

    @final
    def get_dependency(self, name: str) -> "ServiceType":
        """
        Get named dependency if it exists.

        Args:
            name: Dependency name to retrieve

        Returns:
            Dependency service
        """
        raise HandlerNotImplemented

    @final
    def get_dependencies(self) -> dict[str, "ServiceType"]:
        """
        Get all service dependencies.

        Returns:
            Dict mapping dependency names to services
        """
        raise HandlerNotImplemented

    @final
    def get_dependents(self) -> set["ServiceType"]:
        """
        Get all dependent services.

        Returns:
            Set of services depending on this one
        """
        raise HandlerNotImplemented

    @final
    def detach_dependent(self, dependent: "ServiceType") -> None:
        """
        Remove a dependent service.

        Args:
            dependent: Dependent service to remove
        """
        raise HandlerNotImplemented


@runtime_checkable
class ServiceCommonProtocol(
    ServiceCommonBaseProtocol,
    ServiceComposerProtocol,
    Protocol,
):
    pass


@runtime_checkable
class ServiceAsyncProtocol(
    ServiceCommonProtocol,
    ServiceInitializerAsyncProtocol,
    Protocol,
):
    """
    Service protocol.

    This protocol defines the interface for services.

    ATM, no methods are defined, this is a placeholder for future use.
    """

    pass


@runtime_checkable
class ServiceSyncProtocol(
    ServiceCommonProtocol,
    ServiceInitializerSyncProtocol,
    Protocol,
):
    """
    Sync service protocol.

    This protocol defines the interface for services.

    ATM, no methods are defined, this is a placeholder for future use.
    """

    pass
