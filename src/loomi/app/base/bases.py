"""
Base app classes providing asynchronous and synchronous app implementations.

This module defines the foundational app base classes that implement common
functionality for both async and sync app patterns. The classes inherit from
AppCommon to share core app functionality while implementing their
respective protocols.

Classes:
    App: Base class for all apps (common functionality)
    SyncApp: Base class for synchronous apps
    AsyncApp: Base class for asynchronous apps
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from loomi.app.protocols import AppProtocol, AsyncAppProtocol, SyncAppProtocol

from .common import AppCommon

if TYPE_CHECKING:
    from loomi.service import AsyncService, SyncService

__all__ = [
    "SyncApp",
    "AsyncApp",
    "App",
]


class App(AppCommon, AppProtocol):
    """
    Base class providing common functionality for all app types.

    This class implements the core features needed by all apps, whether
    async or sync. It handles service management, identity management,
    and basic app properties.
    """

    pass


class SyncApp(App, SyncAppProtocol):
    """
    Base class for synchronous apps.

    This class combines common app functionality from AppCommon
    with the sync interface defined in SyncAppProtocol. It serves as
    the foundation for all synchronous app implementations.

    The class inherits core app features like service management,
    identity handling, and basic app properties while adding the sync
    protocol requirements.
    """

    _services: dict[str, "SyncService"]
    _app_deps: dict[str, "SyncApp"]


class AsyncApp(App, AsyncAppProtocol):
    """
    Base class for asynchronous apps.

    This class combines common app functionality from AppCommon
    with the async interface defined in AsyncAppProtocol. It serves as
    the foundation for all asynchronous app implementations.

    The class inherits core app features like service management,
    identity handling, and basic app properties while adding the async
    protocol requirements.
    """

    _services: dict[str, "AsyncService"]
    _app_deps: dict[str, "AsyncApp"]
