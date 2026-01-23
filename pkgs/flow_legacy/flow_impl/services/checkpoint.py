"""Cancellation service for flow execution control."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

import attrs

from ..shapes import FlowState
from ._base import ServiceBase


if TYPE_CHECKING:
    from pv.storage import StorageContextType

    from ..types import Path


__all__ = ["CheckpointService"]


@attrs.frozen
class CheckpointService(ServiceBase):
    """Service for managing flow step checkpoints."""

    def set_started(
        self,
        path: Path,
        *,
        storage_context: StorageContextType | None = None,
    ) -> None:
        """Mark checkpoint as started."""
        with self.storage.context() as ctx:
            FlowState.steps[path.to_key()].checkpoint.started.set(True).execute(ctx)
            FlowState.steps[path.to_key()].checkpoint.started_at.set(time.time()).execute(ctx)

    def set_finished(
        self,
        path: Path,
        *,
        storage_context: StorageContextType | None = None,
    ) -> None:
        """Mark checkpoint as finished."""
        with self.storage.context() as ctx:
            FlowState.steps[path.to_key()].checkpoint.finished.set(True).execute(ctx)
            FlowState.steps[path.to_key()].checkpoint.finished_at.set(time.time()).execute(ctx)

    def set_error(
        self,
        path: Path,
        error: str,
        *,
        storage_context: StorageContextType | None = None,
    ) -> None:
        """Mark checkpoint as errored."""
        with self.storage.context() as ctx:
            FlowState.steps[path.to_key()].checkpoint.errored.set(True).execute(ctx)
            FlowState.steps[path.to_key()].checkpoint.error_message.set(error).execute(ctx)
            FlowState.steps[path.to_key()].checkpoint.errored_at.set(time.time()).execute(ctx)
