from __future__ import annotations

from typing import TypeVar

from loomi.interfaces.executor.protocols import AsyncEngineProtocol, SyncEngineProtocol
from loomi.interfaces.state.protocols import AsyncStateProtocol, SyncStateProtocol

__all__ = [
    "StateProtocolT",
    "ExecutorProtocolT",
]

StateProtocolT = TypeVar("StateProtocolT", bound=AsyncStateProtocol | SyncStateProtocol)
ExecutorProtocolT = TypeVar("ExecutorProtocolT", bound=AsyncEngineProtocol | SyncEngineProtocol)
