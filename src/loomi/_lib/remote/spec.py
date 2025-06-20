"""
Remote resource specification and configuration.

This module extends Loomi's Spec system to support remote resource configuration.
"""

from typing import Any, Callable, Optional

from loomi._lib.resource.spec import Spec, SpecField

__all__ = [
    "RemoteConfig",
    "RemoteSpec",
]


class RemoteConfig:
    """Configuration for remote resource access."""

    def __init__(
        self,
        connection_factory: Callable[[], Any],
        resource_name: Optional[str] = None,
    ):
        """
        Initialize remote configuration.

        Args:
            connection_factory: Function that creates and returns a connection
            resource_name: Name of the resource on the server (defaults to class name)
        """
        self.connection_factory = connection_factory
        self.resource_name = resource_name

    def __repr__(self) -> str:
        return f"RemoteConfig(resource_name={self.resource_name})"


class RemoteSpec(Spec):
    """Enhanced spec that supports remote configuration."""

    remote_config: Optional[RemoteConfig] = SpecField(default=None)

    def as_remote(
        self,
        connection_factory: Callable[[], Any],
        resource_name: Optional[str] = None,
    ) -> "RemoteSpec":
        """
        Convert this spec to target a remote resource.

        Args:
            connection_factory: Function that creates and returns a connection
            resource_name: Name of the resource on the server

        Returns:
            New spec configured for remote access

        Example:
            >>> def create_connection():
            ...     import rpyc
            ...     return rpyc.connect("localhost", 18861)
            >>>
            >>> remote_spec = spec.as_remote(create_connection)
        """
        # Create new spec with remote config
        new_spec = self.model_copy()
        new_spec.remote_config = RemoteConfig(
            connection_factory=connection_factory,
            resource_name=resource_name,
        )
        return new_spec

    @property
    def is_remote(self) -> bool:
        """Check if this spec is configured for remote access."""
        return self.remote_config is not None
