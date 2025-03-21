"""
This subpackage provides the foundational classes for building
applications. It includes the base classes for both
synchronous and asynchronous applications, as well as common functionality
shared across different app types.

Modules:
- `bases`: Defines the base classes for applications.
- `common`: Provides common functionality for all app types.

Classes:
- `App`: Base class for all applications.
- `SyncApp`: Base class for synchronous applications.
- `AsyncApp`: Base class for asynchronous applications.
"""

from __future__ import annotations

from .bases import App, AsyncApp, SyncApp
from .meta import AppMeta

__all__ = [
    "AsyncApp",
    "SyncApp",
    "App",
    "AppMeta",
]
