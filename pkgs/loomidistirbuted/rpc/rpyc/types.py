# loomistd/rpyc/_types.py
"""
Type definitions for RPyC implementation.

This module defines types used throughout the RPyC implementation
for consistency and type safety.
"""

from __future__ import annotations

from typing import Any, Dict, TypeAlias

__all__ = [
    "RPyCConfig",
    "ResourceKey",
    "ResourceFactoryName",
    "ResourceRegistry",
]

# RPyC configuration type
RPyCConfig: TypeAlias = Dict[str, Any]

# Resource identification types
ResourceKey: TypeAlias = str
ResourceFactoryName: TypeAlias = str
ResourceRegistry: TypeAlias = Dict[ResourceKey, ResourceFactoryName]
