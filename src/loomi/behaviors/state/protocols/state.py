from __future__ import annotations

from typing import Protocol

from .tree import AsyncStateProtocol, SyncStateProtocol

__all__ = [
    "AsyncStateServiceProtocol",
    "SyncStateServiceProtocol",
]


class AsyncStateServiceProtocol(Protocol):
    """Protocol for asynchronous state service."""

    @property
    def state(self) -> AsyncStateProtocol: ...


class SyncStateServiceProtocol(Protocol):
    """Protocol for synchronous state service."""

    @property
    def state(self) -> SyncStateProtocol: ...
