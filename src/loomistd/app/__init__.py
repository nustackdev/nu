from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from loomi.microflow import AsyncMicroflow, SyncMicroflow
from loomicore.attach import Attach
from loomistd.logger.protocols import AsyncLoggerProtocol, SyncLoggerProtocol
from loomistd.runtime import Runtime
from loomistd.state import State


class SyncApp(SyncMicroflow):
    logger: SyncLoggerProtocol = Attach(optional=True)
    state: State = Attach(optional=True)
    runtime: Runtime = Attach(optional=True)


class AsyncApp(AsyncMicroflow):
    logger: AsyncLoggerProtocol = Attach(optional=True)
    state: State = Attach(optional=True)
    runtime: Runtime = Attach(optional=True)
