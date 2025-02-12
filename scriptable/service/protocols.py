from __future__ import annotations

from types import TracebackType
from typing import TYPE_CHECKING, Any, Protocol, Self, runtime_checkable

if TYPE_CHECKING:
    from .base import Service, ServiceKey, ServiceState, Spec

__all__ = [
    "CommonServiceProtocol",
    "SyncServiceInitializerProtocol",
    "AsyncServiceInitializerProtocol",
    "ServiceComposerProtocol",
    "ServiceProtocol",
    "AsyncServiceProtocol",
    "SyncServiceProtocol",
]


@runtime_checkable
class CommonServiceProtocol(Protocol):
    @classmethod
    def factory_name(cls) -> str: ...

    @property
    def spec(self) -> "Spec": ...

    @property
    def name(self) -> str: ...

    @property
    def readable_name(self) -> str: ...

    @property
    def key(self) -> "ServiceKey": ...

    @property
    def service_state(self) -> "ServiceState": ...

    @property
    def is_initialized(self) -> bool: ...

    def __hash__(self) -> int:
        """Hash based on service key."""
        ...

    def __eq__(self, other: Any) -> bool:
        """Equality based on service key."""
        ...

    def __repr__(self) -> str:
        """String representation including spec."""
        ...


@runtime_checkable
class SyncServiceInitializerProtocol(Protocol):
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


@runtime_checkable
class AsyncServiceInitializerProtocol(Protocol):
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


@runtime_checkable
class ServiceComposerProtocol(Protocol):
    """
    Async service composer protocol.

    This protocol defines the interface for services composition.

    ATM, no methods are defined, this is a placeholder for future use.
    """

    def add_dependency(
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

    def get_dependency(self, name: str) -> "Service":
        """
        Get named dependency if it exists.

        Args:
            name: Dependency name to retrieve

        Returns:
            Dependency service
        """
        ...

    def get_dependencies(self) -> dict[str, "Service"]:
        """
        Get all service dependencies.

        Returns:
            Dict mapping dependency names to services
        """
        ...

    def get_dependents(self) -> set["Service"]:
        """
        Get all dependent services.

        Returns:
            Set of services depending on this one
        """
        ...

    def detach_dependent(self, dependent: "Service") -> None:
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


@runtime_checkable
class ServiceProtocol(
    CommonServiceProtocol,
    ServiceComposerProtocol,
    Protocol,
):
    pass


@runtime_checkable
class AsyncServiceProtocol(
    ServiceProtocol,
    AsyncServiceInitializerProtocol,
    Protocol,
):
    """
    Async service protocol.

    This protocol defines the interface for async services.
    """

    pass


@runtime_checkable
class SyncServiceProtocol(
    ServiceProtocol,
    SyncServiceInitializerProtocol,
    Protocol,
):
    """
    Sync service protocol.

    This protocol defines the interface for sync services.
    """

    pass
