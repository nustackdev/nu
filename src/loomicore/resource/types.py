"""
Resource type definitions for internal use.

This module defines type aliases and forward references for resource types
to avoid circular imports between the resource module and runtime system.

The resource module cannot import from runtime (would create circular imports)
but runtime needs to reference resource types. This module provides the
bridge using TYPE_CHECKING imports and string type annotations.

Type Aliases:
    SyncResourceType: Forward reference to SyncResource
    AsyncResourceType: Forward reference to AsyncResource
    ResourceType: Union type for any resource

Design Notes:
    - Uses TYPE_CHECKING to avoid runtime imports
    - String annotations prevent circular import errors
    - Allows runtime to reference resource types safely
    - Keeps dependency hierarchy clean
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

# Type aliases for runtime system (avoids circular imports)
SyncResourceType = "SyncResource"
AsyncResourceType = "AsyncResource"
ResourceType = "SyncResource | AsyncResource"

# Export for runtime usage
__all__ = [
    "SyncResourceType",
    "AsyncResourceType",
    "ResourceType",
]
