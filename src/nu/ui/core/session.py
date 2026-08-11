"""Abstract session interface for nu.ui hosts.

A Session is the wire-transport handle that Refs resolve through: send a
Frame, round-trip a read, subscribe to change notifications. Concrete
hosts (nudle over ws, and future ones) implement this contract; widget
code and interactions target the abstract shape so the widget kit is
reusable across hosts.

Bound on Context by the host (`ctx.bind(Session, concrete)`). Widget
code calls `rt.ctx.get(Session)`.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Protocol


if TYPE_CHECKING:
    from collections.abc import Callable

    from .protocol import Frame


__all__ = ["Session", "Subscription"]


class Subscription(Protocol):
    """Observer handle returned by `session.subscribe(path)`.

    Same shape as nu-kv' subscription handle. React / ReactForever
    bind callbacks on it; the session fires them when a `notify` frame
    lands from the browser for the subscribed path.
    """

    def bind(self, cb: Callable[[object], None]) -> None: ...

    def unbind(self, cb: Callable[[object], None]) -> None: ...

    def close(self) -> None: ...


class Session(ABC):
    """Abstract wire transport for a mounted UI.

    One instance per client connection. Owned by the host; bound on
    Context so Refs and interactions can reach it.
    """

    @abstractmethod
    async def send(self, frame: Frame) -> None:
        """Ship a Frame to the client."""

    @abstractmethod
    async def aread(self, path: str) -> Any:
        """Round-trip: ship a read frame, await the client's reply."""

    @abstractmethod
    def subscribe(self, path: str) -> Subscription:
        """Register interest in change notifications for `path`."""
