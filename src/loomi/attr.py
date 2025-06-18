from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar, cast

from ._lib.resource import ResourceDescriptor, Spec

if TYPE_CHECKING:
    from loomi.app import AsyncApp, SyncApp
    from loomi.service import AsyncService, SyncService


App = TypeVar("App", bound="AsyncApp | SyncApp")
Service = TypeVar("App", bound="AsyncService | SyncService")


def UseApp(app: type[App], spec: "Spec | None" = None) -> App:
    """Create a service specification."""
    return cast(App, ResourceDescriptor[App](spec))


def UseService(spec: "Spec | None" = None) -> Service:
    """Create a service specification."""
    return cast(Service, ResourceDescriptor[Service](spec))


__all__ = [
    "UseApp",
    "UseService",
]
