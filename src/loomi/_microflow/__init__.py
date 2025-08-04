from __future__ import annotations

from loomicore.resource import AsyncResource, BaseResource, Resource, SyncResource

__all__ = [
    "BaseMicroflow",
    "SyncMicroflow",
    "AsyncMicroflow",
    "Microflow",
]


class BaseMicroflow(BaseResource):
    """
    Base class for all Loomi components.

    This class provides the basic functionality for components, including lifecycle management.
    Microflows can be synchronous or asynchronous, depending on the implementation.
    """

    pass


class SyncMicroflow(BaseMicroflow, SyncResource):
    """
    Synchronous component with lifecycle management.

    This class provides synchronous lifecycle methods and dependency injection for components.
    It is designed for use in synchronous applications where blocking operations are acceptable.
    """

    pass


class AsyncMicroflow(BaseMicroflow, AsyncResource):
    """
    Asynchronous component with lifecycle management.

    This class provides asynchronous lifecycle methods and dependency injection for components.
    It is designed for use in asynchronous applications where non-blocking operations are preferred.
    """

    pass


Microflow = SyncMicroflow | AsyncMicroflow
