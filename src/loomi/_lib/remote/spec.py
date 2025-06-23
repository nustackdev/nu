"""
Remote resource specification and configuration.

This module provides a wrapper around regular specs to support remote
resource configuration while keeping local specs clean and serializable.
"""

import pickle
from typing import Any, Callable, Optional

from loomi._lib.resource.spec import Spec

__all__ = [
    "RemoteConfig",
    "RemoteSpec",
    "serialize_spec",
    "deserialize_spec",
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


class RemoteSpec:
    """
    Wrapper around a local spec that adds remote configuration.

    This approach keeps the local spec clean and serializable while
    adding remote capabilities as a separate layer.
    """

    def __init__(self, local_spec: Spec, remote_config: RemoteConfig):
        """
        Initialize remote spec wrapper.

        Args:
            local_spec: The actual spec for the resource
            remote_config: Remote connection configuration
        """
        self.local_spec = local_spec
        self.remote_config = remote_config

    @property
    def factory(self):
        """Delegate factory to local spec."""
        return self.local_spec.factory

    @property
    def name(self):
        """Delegate name to local spec."""
        return self.local_spec.name

    @property
    def key(self):
        """Delegate key to local spec."""
        return self.local_spec.key

    @property
    def is_remote(self) -> bool:
        """This is always a remote spec."""
        return True

    def __getattr__(self, name):
        """Delegate all other attributes to local spec."""
        return getattr(self.local_spec, name)

    def __repr__(self) -> str:
        return f"RemoteSpec(local_spec={self.local_spec}, remote_config={self.remote_config})"


# Add as_remote method to regular Spec class
def as_remote(
    self: Spec,
    connection_factory: Callable[[], Any],
    resource_name: Optional[str] = None,
) -> RemoteSpec:
    """
    Convert this spec to target a remote resource.

    Args:
        connection_factory: Function that creates and returns a connection
        resource_name: Name of the resource on the server

    Returns:
        RemoteSpec wrapping this spec

    Example:
        >>> import rpyc
        >>> def create_connection():
        ...     return rpyc.connect("localhost", 18861)
        >>>
        >>> remote_spec = spec.as_remote(create_connection)
    """
    remote_config = RemoteConfig(
        connection_factory=connection_factory,
        resource_name=resource_name,
    )
    return RemoteSpec(self, remote_config)


# Monkey patch the as_remote method onto Spec
Spec.as_remote = as_remote


def serialize_spec(spec: Spec) -> bytes:
    """
    Serialize a spec for transmission over the network.

    Args:
        spec: Spec to serialize

    Returns:
        Serialized spec data
    """
    return pickle.dumps(spec)


def deserialize_spec(data: bytes) -> Spec:
    """
    Deserialize a spec from network data.

    Args:
        data: Serialized spec data

    Returns:
        Reconstructed spec
    """
    return pickle.loads(data)
