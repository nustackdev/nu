from __future__ import annotations

from typing import Protocol

from loomi.microflow import AsyncMicroflow, SyncMicroflow
from loomicore.attach import Attach
from loomistd.logger.protocols import AsyncLoggerProtocol, SyncLoggerProtocol
from loomistd.runtime import Runtime
from loomistd.state import State

__all__ = [
    "SyncApp",
    "AsyncApp",
    "SyncAppProtocol",
    "AsyncAppProtocol",
]


class SyncApp(SyncMicroflow):
    logger: SyncLoggerProtocol = Attach(optional=True)
    state: State = Attach(optional=True)
    runtime: Runtime = Attach(optional=True)


class AsyncApp(AsyncMicroflow):
    logger: AsyncLoggerProtocol = Attach(optional=True)
    state: State = Attach(optional=True)
    runtime: Runtime = Attach(optional=True)


class SyncAppProtocol(Protocol):
    """
    Protocol for synchronous applications.
    This protocol defines the expected interface for synchronous applications.
    """

    logger: SyncLoggerProtocol
    state: State
    runtime: Runtime


class AsyncAppProtocol(Protocol):
    """
    Protocol for asynchronous applications.
    This protocol defines the expected interface for asynchronous applications.
    """

    logger: AsyncLoggerProtocol
    state: State
    runtime: Runtime
