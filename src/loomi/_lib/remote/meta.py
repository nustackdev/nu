"""
Remote resource metaclass for transparent remote resource creation.

This metaclass intercepts resource creation and routes to remote servers
when specs are configured for remote access, making remote resources
completely transparent to application code.
"""

from loomi._lib.resource.meta import ResourceMeta

from .logger import logger
from .spec import RemoteSpec, serialize_spec

__all__ = [
    "RemoteResourceMeta",
]


class RemoteResourceMeta(ResourceMeta):
    """
    Enhanced ResourceMeta that transparently creates remote resources.

    This metaclass preserves all existing Loomi behavior while adding
    the ability to create remote resource proxies when configured.
    """

    def __call__(cls, spec=None, *args, **kwargs):
        """
        Create resource instance, transparently handling remote specs.

        Args:
            spec: Resource specification (may be remote)
            *args: Additional arguments
            **kwargs: Additional keyword arguments

        Returns:
            Resource instance (local or remote proxy)
        """
        # Handle remote specs transparently
        if spec is not None and isinstance(spec, RemoteSpec) and spec.is_remote:
            return cls._create_remote_resource(spec, *args, **kwargs)

        # Normal local resource creation
        return super().__call__(spec, *args, **kwargs)

    def _create_remote_resource(cls, spec: RemoteSpec, *args, **kwargs):
        """
        Create a remote resource proxy transparently.

        Args:
            spec: Remote resource specification
            *args: Additional arguments (ignored for remote)
            **kwargs: Additional keyword arguments (ignored for remote)

        Returns:
            Remote resource proxy wrapped for autocomplete
        """
        logger.debug(
            f"Creating remote resource: {cls.__name__} with spec: {spec} and local spec: {spec.local_spec}"
        )
        try:
            # Create connection to remote server
            connection = spec.remote_config.connection_factory()

            # Use the clean local spec for the server
            local_spec = spec.local_spec

            # Serialize the local spec for transmission
            spec_data = serialize_spec(local_spec)

            # Create the remote resource
            remote_proxy = connection.root.create_resource(spec_data)

            # Wrap proxy for IDE autocomplete support
            return remote_proxy
            # return wrap_remote_resource(cls, remote_proxy)

        except Exception as e:
            raise RuntimeError(f"Failed to create remote resource {cls.__name__}: {e}") from e
