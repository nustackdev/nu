from __future__ import annotations

from .descriptors import Attach, ResourceDescriptor
from .resource import (
    AsyncResource,
    AsyncResourceABC,
    Resource,
    ResourceABC,
    ResourceMeta,
    SyncResource,
    SyncResourceABC,
)
from .spec import Spec

__all__ = [
    "ResourceMeta",
    "ResourceABC",
    "SyncResourceABC",
    "AsyncResourceABC",
    "Resource",
    "SyncResource",
    "AsyncResource",
    "Attach",
    "ResourceDescriptor",
    "Spec",
]
