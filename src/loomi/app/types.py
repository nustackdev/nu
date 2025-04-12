from __future__ import annotations

from typing import TypeVar

from loomi.interfaces.executor.protocols import AsyncEngineProtocol, SyncEngineProtocol
from loomi.interfaces.state.protocols import AsyncStateProtocol, SyncStateProtocol

__all__ = [
    "ST",
    "ET",
]

ST = TypeVar("ST", bound=AsyncStateProtocol | SyncStateProtocol)
ET = TypeVar("ET", bound=AsyncEngineProtocol | SyncEngineProtocol)

SyncST = TypeVar("SyncST", bound=SyncStateProtocol)
SyncET = TypeVar("SyncET", bound=SyncEngineProtocol)
