"""
Resource module public API.

This module provides the main resource classes for Loomi applications.
Resources are the primary building blocks for composable, dependency-injected
services with automatic lifecycle management.

Classes:
    BaseResource: Common functionality shared by all resource types
    SyncResource: Synchronous resource with blocking lifecycle methods
    AsyncResource: Asynchronous resource with async lifecycle methods
    Resource: Type union of SyncResource | AsyncResource

Example:
    ```python
    from loomicore.resource import SyncResource
    from loomicore.patterns.attach import Attach

    class DatabaseService(SyncResource):
        cache = Attach(CacheSpec())

        def setup(self):
            self.cache.initialize()

        def cleanup(self):
            self.cache.shutdown()

    # Usage
    with DatabaseService(spec) as db:
        db.query("SELECT * FROM users")
    ```

Design Philosophy:
    - Ultra-thin interface that delegates to Runtime system
    - Clear separation between user interface and implementation
    - Direct types (not protocols) for simplicity
    - OS library approach - provide concrete building blocks

Notes:
    All operational logic (creation, dependency resolution, lifecycle management)
    is handled by the Runtime system. Resource classes provide only the user
    interface and delegate everything else.
"""

from __future__ import annotations

from .base import BaseResource
from .resource import SyncResource
from .resource_async import AsyncResource

# Type union for generic resource handling
Resource = SyncResource | AsyncResource

__all__ = [
    "BaseResource",
    "SyncResource",
    "AsyncResource",
    "Resource",
]
