"""
Dynamic wrapper for remote resources to provide autocomplete.

This module implements your clever wrapper idea to provide IDE autocomplete
for remote resources while forwarding all calls to the actual RPyC proxy.
"""

from __future__ import annotations

from typing import Any, Type, TypeVar, cast

import wrapt

__all__ = [
    "DynamicRemoteWrapper",
    "wrap_remote_resource",
]

ResourceT = TypeVar("ResourceT")


class DynamicRemoteWrapper(wrapt.ObjectProxy):
    """
    Base wrapper that forwards all calls to the wrapped RPyC proxy
    while appearing as the original resource type to IDEs.
    """

    def __init__(self, wrapped_proxy: Any):
        """
        Initialize wrapper with RPyC proxy.

        Args:
            wrapped_proxy: The RPyC proxy object to wrap
        """
        super().__init__(wrapped_proxy)
        # Store reference to avoid infinite recursion
        self._self_proxy = wrapped_proxy


def construct_wrapper_class(
    resource_type: Type[ResourceT], proxy_type: Type[Any]
) -> Type[DynamicRemoteWrapper]:
    """
    Dynamically construct a wrapper class for the given resource type.

    This creates a class that inherits from both the resource type
    (for IDE autocomplete) and DynamicRemoteWrapper (for forwarding).

    Args:
        resource_type: The original resource type (for autocomplete)
        proxy_type: The proxy type (usually RPyC proxy)

    Returns:
        Wrapper class that appears as resource_type but forwards to proxy
    """

    class TypedRemoteWrapper(DynamicRemoteWrapper, resource_type):
        """
        Dynamically created wrapper that provides type information
        while forwarding all operations to the remote proxy.
        """

        def __init__(self, wrapped_proxy: Any):
            # Only call DynamicRemoteWrapper.__init__ to avoid
            # calling resource_type.__init__ which would create a local instance
            DynamicRemoteWrapper.__init__(self, wrapped_proxy)

    # Set proper class name for debugging
    TypedRemoteWrapper.__name__ = f"Remote{resource_type.__name__}"
    TypedRemoteWrapper.__qualname__ = f"Remote{resource_type.__qualname__}"

    return TypedRemoteWrapper


def wrap_remote_resource(resource_type: Type[ResourceT], remote_proxy: Any) -> ResourceT:
    """
    Wrap a remote proxy with type information for autocomplete.

    Args:
        resource_type: The resource type to appear as
        remote_proxy: The actual RPyC proxy

    Returns:
        Wrapped proxy that provides autocomplete as resource_type

    Example:
        >>> proxy = rpyc_connection.root.create_resource(spec_data)
        >>> typed_proxy = wrap_remote_resource(StateService, proxy)
        >>> # Now typed_proxy appears as StateService to IDE
        >>> typed_proxy.initialize()  # Autocomplete works!
    """
    # Get or create wrapper class for this resource type
    if not hasattr(resource_type, "_remote_wrapper_class"):
        wrapper_class = construct_wrapper_class(resource_type, type(remote_proxy))
        setattr(resource_type, "_remote_wrapper_class", wrapper_class)
    else:
        wrapper_class = getattr(resource_type, "_remote_wrapper_class")

    # Create and return wrapped instance
    return cast(ResourceT, wrapper_class(remote_proxy))


# Alternative approach: Class method on resources
class RemoteResourceMixin:
    """
    Mixin that can be added to resource classes to provide
    a convenient .from_remote() class method.
    """

    @classmethod
    def from_remote(cls: Type[ResourceT], remote_proxy: Any) -> ResourceT:
        """
        Create a typed wrapper around a remote proxy.

        Args:
            remote_proxy: RPyC proxy from remote server

        Returns:
            Wrapped proxy with full type information

        Example:
            >>> proxy = connection.root.create_resource(spec_data)
            >>> state_service = StateService.from_remote(proxy)
        """
        return wrap_remote_resource(cls, remote_proxy)
