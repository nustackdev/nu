"""Type definitions for Invisibles RPC resources."""

from __future__ import annotations


__all__ = [
    "ResourceFactoryName",
    "ResourceKey",
    "ResourceRegistry",
]

# Resource identification types
type ResourceKey = str
type ResourceFactoryName = str
type ResourceRegistry = dict[ResourceKey, ResourceFactoryName]
