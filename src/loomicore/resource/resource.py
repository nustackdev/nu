from __future__ import annotations

from .composer import AsyncResourceComposer, SyncResourceComposer
from .initializer import AsyncResourceInitializer, SyncResourceInitializer
from .meta import ResourceMeta

__all__ = [
    "AsyncResource",
    "SyncResource",
    "Resource",
]


class AsyncResource(
    AsyncResourceComposer,
    AsyncResourceInitializer,
    metaclass=ResourceMeta,
):
    pass


class SyncResource(
    SyncResourceComposer,
    SyncResourceInitializer,
    metaclass=ResourceMeta,
):
    pass


Resource = AsyncResource | SyncResource
