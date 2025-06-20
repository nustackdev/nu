"""
Remote-enabled resource base classes.

This module provides resource base classes that automatically support
remote access when configured with remote specs.
"""

from loomi._lib.resource import AsyncResource as BaseAsyncResource
from loomi._lib.resource import SyncResource as BaseSyncResource

from .meta import RemoteResourceMeta
from .spec import RemoteSpec

__all__ = [
    "AsyncResource",
    "SyncResource",
    "RemoteSpec",
]


class AsyncResource(BaseAsyncResource, metaclass=RemoteResourceMeta):
    """AsyncResource with automatic remote capability."""

    pass


class SyncResource(BaseSyncResource, metaclass=RemoteResourceMeta):
    """SyncResource with automatic remote capability."""

    pass
