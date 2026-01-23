"""Type definitions for RPyC implementation.

This module defines types used throughout the RPyC implementation
for consistency and type safety.
"""

from __future__ import annotations

from typing import Any


__all__ = [
    "RPyCConfig",
    "ResourceFactoryName",
    "ResourceKey",
    "ResourceRegistry",
]

# RPyC configuration type
type RPyCConfig = dict[str, Any]

# Resource identification types
type ResourceKey = str
type ResourceFactoryName = str
type ResourceRegistry = dict[ResourceKey, ResourceFactoryName]
