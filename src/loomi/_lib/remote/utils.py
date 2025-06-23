from __future__ import annotations

from typing import Any, Generic, Optional, Type, TypeVar

from loomi._lib.resource import Spec

from .client.client import create_remote_resource

ResourceT = TypeVar("ResourceT")

__all__ = [
    "remote_tcp",
    "remote_unix",
    "remote_resource",
]


def remote_tcp(
    spec: Spec,
    resource_type: Optional[Type[ResourceT]] = None,
    host: str = "localhost",
    port: int = 18861,
    **rpyc_config,
) -> Any:
    """
    Create a remote resource via TCP connection.

    Args:
        spec: Resource specification
        resource_type: Optional type for autocomplete wrapper
        host: Server hostname
        port: Server port
        **rpyc_config: Additional RPyC configuration

    Returns:
        Remote resource proxy

    Example:
        >>> from loomistd.state import StateService, StateSpec
        >>> spec = StateSpec()
        >>> remote_state = remote_tcp(spec, StateService, host="server", port=8080)
        >>> remote_state.initialize()  # Works with autocomplete!
    """
    return create_remote_resource(
        spec=spec, resource_type=resource_type, host=host, port=port, **rpyc_config
    )


def remote_unix(
    spec: Spec,
    resource_type: Optional[Type[ResourceT]] = None,
    socket_path: str = "/tmp/loomi.sock",
    **rpyc_config,
) -> Any:
    """
    Create a remote resource via Unix socket connection.

    Args:
        spec: Resource specification
        resource_type: Optional type for autocomplete wrapper
        socket_path: Unix socket path
        **rpyc_config: Additional RPyC configuration

    Returns:
        Remote resource proxy

    Example:
        >>> from loomistd.state import StateService, StateSpec
        >>> spec = StateSpec()
        >>> remote_state = remote_unix(spec, StateService, "/tmp/state.sock")
        >>> remote_state.initialize()
    """
    return create_remote_resource(
        spec=spec, resource_type=resource_type, socket_path=socket_path, **rpyc_config
    )


def remote_resource(
    resource_class: Type[ResourceT],
    spec: Optional[Spec] = None,
    host: Optional[str] = None,
    port: Optional[int] = None,
    socket_path: Optional[str] = None,
    **rpyc_config,
) -> ResourceT:
    """
    Create a remote resource with automatic spec and type handling.

    Args:
        resource_class: Resource class to create
        spec: Optional spec (uses default if not provided)
        host: Server hostname (for TCP)
        port: Server port (for TCP)
        socket_path: Unix socket path (takes precedence)
        **rpyc_config: Additional RPyC configuration

    Returns:
        Typed remote resource proxy

    Example:
        >>> # Simple remote resource creation
        >>> state_service = remote_resource(
        ...     StateService,
        ...     socket_path="/tmp/state.sock"
        ... )
        >>> state_service.initialize()  # Full autocomplete support
    """
    # Use provided spec or create default
    if spec is None:
        spec = Spec(factory=resource_class)

    return create_remote_resource(
        spec=spec,
        resource_type=resource_class,
        host=host,
        port=port,
        socket_path=socket_path,
        **rpyc_config,
    )


class RemoteResourceBuilder(Generic[ResourceT]):
    """
    Builder pattern for remote resource creation.

    Provides a fluent interface for configuring remote resources.
    """

    def __init__(self, resource_class: Type[ResourceT]):
        self.resource_class = resource_class
        self.spec = None
        self.connection_params = {}
        self.rpyc_config = {}

    def with_spec(self, spec: Spec) -> "RemoteResourceBuilder[ResourceT]":
        """Set the resource specification."""
        self.spec = spec
        return self

    def via_tcp(
        self, host: str = "localhost", port: int = 18861
    ) -> "RemoteResourceBuilder[ResourceT]":
        """Configure TCP connection."""
        self.connection_params = {"host": host, "port": port}
        return self

    def via_unix(self, socket_path: str) -> "RemoteResourceBuilder[ResourceT]":
        """Configure Unix socket connection."""
        self.connection_params = {"socket_path": socket_path}
        return self

    def with_rpyc_config(self, **config) -> "RemoteResourceBuilder[ResourceT]":
        """Set RPyC configuration."""
        self.rpyc_config.update(config)
        return self

    def build(self) -> ResourceT:
        """Create the remote resource."""
        spec = self.spec or Spec(factory=self.resource_class)

        return create_remote_resource(
            spec=spec,
            resource_type=self.resource_class,
            **self.connection_params,
            **self.rpyc_config,
        )
