from __future__ import annotations

from typing import Protocol, TypeVar

from loomicore.attach import Attach
from loomicore.resource import AsyncResource, BaseResource, Resource, SyncResource

from .._tree.tree import Tree

__all__ = [
    "BaseMicroflow",
    "SyncMicroflow",
    "AsyncMicroflow",
    "Microflow",
    "MicroflowT",
]


class State(Protocol):
    @property
    def tree(self) -> Tree: ...


class BaseMicroflow(BaseResource):
    """
    Base class for all Loomi components.

    This class provides the basic functionality for components, including lifecycle management.
    Microflows can be synchronous or asynchronous, depending on the implementation.
    """

    state: State = Attach()


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


class MicroflowProtocol(Protocol):
    """
    Protocol for microflow components.

    This protocol defines the basic interface for microflow components, allowing for type checking
    and ensuring that implementations provide the necessary methods.
    """

    state: State


Microflow = SyncMicroflow | AsyncMicroflow
MicroflowT = TypeVar("MicroflowT", bound=Microflow | MicroflowProtocol)
