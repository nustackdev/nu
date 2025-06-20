"""
Remote resource system for Loomi.

This package provides transparent remote access to Loomi resources through
a thin layer over existing communication libraries like RPyC.
"""

from .resource import AsyncResource, SyncResource
from .spec import RemoteConfig, RemoteSpec

__all__ = [
    # Resource classes
    "AsyncResource",
    "SyncResource",
    # Specification
    "RemoteSpec",
    "RemoteConfig",
]
